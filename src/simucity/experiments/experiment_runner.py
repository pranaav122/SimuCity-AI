"""Reproducible experiment framework, batch comparison runner, and telemetry exporter."""

import time
from typing import Any

from pydantic import BaseModel, Field

from simucity.agents.agent import SimuAgent
from simucity.agents.goals import create_default_goals
from simucity.agents.needs import AgentNeeds
from simucity.agents.personality import Personality
from simucity.core.actions import ActionType, ProposedAction
from simucity.core.clock import SimulationClock
from simucity.core.engine import SimulationEngine
from simucity.core.environment import CampusEnvironment
from simucity.events.event import SimulationEvent
from simucity.events.event_manager import EventManager
from simucity.information.info_propagator import InformationLedger
from simucity.llm.mock_provider import MockLLMProvider
from simucity.llm.provider import LLMProvider
from simucity.metrics.emergence import EmergenceDetector, EmergentPattern
from simucity.metrics.metrics_collector import MetricsCollector, SimulationMetrics
from simucity.social.social_network import SocialGraph
from simucity.utils.rng import SeededRNG

# Action type strings that can appear in LLM structured output
_LLM_ACTION_MAP: dict[str, ActionType] = {
    "move": ActionType.MOVE,
    "wait": ActionType.WAIT,
    "sleep": ActionType.SLEEP,
    "rest": ActionType.REST,
    "eat": ActionType.EAT,
    "study": ActionType.STUDY,
    "attend_class": ActionType.ATTEND_CLASS,
    "work": ActionType.WORK,
    "purchase_item": ActionType.PURCHASE_ITEM,
    "socialize": ActionType.SOCIALIZE,
    "help_agent": ActionType.HELP_AGENT,
    "share_info": ActionType.SHARE_INFO,
}

_AVAILABLE_ACTIONS = list(_LLM_ACTION_MAP.keys())


class ExperimentConfig(BaseModel):
    """Declarative specification of a reproducible simulation experiment."""

    experiment_id: str
    name: str = "Campus Emergence Study"
    number_of_agents: int = Field(default=16, ge=2, le=200)
    simulation_days: int = Field(default=3, ge=1, le=60)
    model: str = Field(default="mock", description="'claude' | 'gemini' | 'mock'")
    event_scenario: str | None = Field(default=None, description="Preset shock event ID")
    seed: int = Field(default=42, description="RNG seed for deterministic reproducibility")


class ExperimentResult(BaseModel):
    """Complete summary outcome of an experiment run."""

    config: ExperimentConfig
    duration_seconds: float
    total_ticks: int
    final_metrics: SimulationMetrics | None = None
    all_metrics: list[SimulationMetrics] = Field(default_factory=list)
    detected_patterns: list[EmergentPattern] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    average_latency_ms: float = 0.0
    agent_summaries: list[dict[str, Any]] = Field(default_factory=list)


def _build_provider(model: str) -> LLMProvider:
    """Constructs the appropriate LLM provider, raising EnvironmentError if keys are absent."""
    if model == "claude":
        from simucity.llm.claude_provider import ClaudeProvider  # noqa: PLC0415

        return ClaudeProvider()
    if model == "gemini":
        from simucity.llm.gemini_provider import GeminiProvider  # noqa: PLC0415

        return GeminiProvider()
    return MockLLMProvider()


class ExperimentRunner:
    """Orchestrates multi-agent simulation experiments with strict reproducibility."""

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config
        self.rng = SeededRNG(config.seed)
        self.clock = SimulationClock(start_day=1, start_hour=8, start_minute=0)
        self.environment = CampusEnvironment.create_default_campus()
        self.engine = SimulationEngine(
            seed=config.seed, environment=self.environment, clock=self.clock
        )
        self.agents: dict[str, SimuAgent] = {}
        self.social_graph = SocialGraph()
        self.info_ledger = InformationLedger()
        self.event_manager = EventManager()
        self.metrics_collector = MetricsCollector()

        # LLM provider — may raise EnvironmentError for claude/gemini with no key
        self.llm_provider: LLMProvider = _build_provider(config.model)
        self._use_llm = config.model in ("claude", "gemini")

        self._setup_population()
        self._setup_events()

    def _setup_population(self) -> None:
        """Instantiates heterogeneous population with diverse personalities and goals."""
        archetypes = ["scholar", "socialite", "entrepreneur", "balanced"]
        names = [
            "Alice",
            "Bob",
            "Charlie",
            "Diana",
            "Ethan",
            "Fiona",
            "George",
            "Hannah",
            "Ian",
            "Julia",
            "Kevin",
            "Luna",
            "Marcus",
            "Nora",
            "Oliver",
            "Piper",
            "Quinn",
            "Riley",
            "Sam",
            "Tara",
            "Umar",
            "Violet",
            "Will",
            "Xena",
        ]

        for i in range(self.config.number_of_agents):
            agent_id = f"agent_{i + 1:02d}"
            name = names[i % len(names)] if i < len(names) else f"Student_{i + 1}"
            archetype = archetypes[i % len(archetypes)]

            if archetype == "scholar":
                p = Personality.scholarly_introvert()
            elif archetype == "socialite":
                p = Personality.social_butterfly()
            elif archetype == "entrepreneur":
                p = Personality.ambitious_entrepreneur()
            else:
                p = Personality.thrifty_slacker()

            p.extroversion = max(0.05, min(0.95, p.extroversion + self.rng.uniform(-0.05, 0.05)))
            p.cooperation = max(0.05, min(0.95, p.cooperation + self.rng.uniform(-0.05, 0.05)))

            initial_money = 100.0 + self.rng.randint(-20, 40)
            initial_loc = "dorm_north" if i % 2 == 0 else "dorm_south"

            agent = SimuAgent(
                agent_id=agent_id,
                name=name,
                age=19 + (i % 4),
                personality=p,
                needs=AgentNeeds(hunger=self.rng.uniform(10, 30), energy=self.rng.uniform(70, 95)),
                goals=create_default_goals(archetype),
                archetype=archetype,
            )

            self.agents[agent_id] = agent
            self.social_graph.add_agent(agent_id)
            self.engine.register_agent(
                agent_id=agent_id,
                initial_location_id=initial_loc,
                initial_money=initial_money,
            )

    def _setup_events(self) -> None:
        """Schedules preset scenario events if specified."""
        if self.config.event_scenario == "cafeteria_price_increase":
            self.event_manager.schedule_event(
                SimulationEvent.cafeteria_price_shock(trigger_tick=96)
            )
        elif self.config.event_scenario == "surprise_midterm":
            self.event_manager.schedule_event(
                SimulationEvent.surprise_midterm_exam(trigger_tick=96)
            )
        elif self.config.event_scenario == "transit_strike":
            self.event_manager.schedule_event(SimulationEvent.transit_strike(trigger_tick=96))

    def _llm_to_proposed_action(
        self, agent_id: str, structured: dict[str, Any] | None, snapshot: Any
    ) -> ProposedAction:
        """Maps an LLM response's structured_data dict to a ProposedAction.

        Falls back to WAIT if the response is absent or unparseable.
        """
        if not structured:
            return ProposedAction(agent_id=agent_id, action_type=ActionType.WAIT)

        raw_type = str(structured.get("action_type", "wait")).lower().strip()
        action_type = _LLM_ACTION_MAP.get(raw_type, ActionType.WAIT)

        target_loc = structured.get("target_location_id") or None
        target_agent = structured.get("target_agent_id") or None
        amount = float(structured.get("amount") or 0.0)

        # Validate target_loc actually exists in the environment
        if target_loc and target_loc not in self.environment.locations:
            target_loc = None
            if action_type == ActionType.MOVE:
                action_type = ActionType.WAIT

        # Validate target_agent is registered
        if target_agent and target_agent not in self.agents:
            target_agent = None
            if action_type in (ActionType.SOCIALIZE, ActionType.HELP_AGENT, ActionType.SHARE_INFO):
                action_type = ActionType.WAIT

        return ProposedAction(
            agent_id=agent_id,
            action_type=action_type,
            target_location_id=target_loc,
            target_agent_id=target_agent,
            amount=amount,
        )

    def _build_env_context(self, agent_id: str, snapshot: Any) -> dict[str, Any]:
        """Builds the environment context dict passed to the LLM for an agent's decision."""
        agent_state = snapshot.agent_states.get(agent_id)
        if not agent_state:
            return {}
        loc = self.environment.get_location(agent_state.location_id)
        co_located = self.environment.get_co_located_agents(agent_id)
        return {
            "time_str": snapshot.time_str,
            "day": snapshot.day,
            "day_of_week": self.clock.day_of_week,
            "location_id": agent_state.location_id,
            "location_name": loc.name if loc else agent_state.location_id,
            "money": agent_state.money,
            "is_class_hours": self.clock.is_class_hours,
            "co_located_agents": co_located,
            "active_events": list(self.engine.active_events),
        }

    def run(self) -> ExperimentResult:
        """Executes the full experiment across the specified simulation duration."""
        t_start = time.perf_counter()
        total_ticks = self.config.simulation_days * self.clock.ticks_per_day

        for _ in range(total_ticks):
            current_tick = self.clock.current_tick

            # 1. Trigger Scheduled Events
            newly_triggered = self.event_manager.tick(current_tick, self.engine)
            for ev in newly_triggered:
                if ev.rumor_content:
                    self.info_ledger.publish_info(
                        info_id=f"info_{ev.id}",
                        topic=ev.title,
                        content=ev.rumor_content,
                        source="OFFICIAL",
                        origin_tick=current_tick,
                    )

            # 2. Synchronize Agent Needs from Engine
            latest_snapshot = self.engine.history[-1] if self.engine.history else None
            if latest_snapshot:
                for agent in self.agents.values():
                    agent.sync_from_snapshot(latest_snapshot)

            # 3. Collect Proposed Actions
            proposed_actions: dict[str, ProposedAction] = {}
            for agent_id, agent in self.agents.items():
                if not latest_snapshot:
                    proposed_actions[agent_id] = ProposedAction(
                        agent_id=agent_id, action_type=ActionType.WAIT
                    )
                    continue

                if self._use_llm:
                    # ── LLM PATH: ask the model to decide ──────────────────────────────
                    agent_profile = agent.to_dict()
                    env_context = self._build_env_context(agent_id, latest_snapshot)
                    memories = [m.model_dump() for m in agent.memory.short_term_buffer[-5:]]
                    llm_resp = self.llm_provider.generate_decision(
                        agent_profile=agent_profile,
                        environment_context=env_context,
                        recent_memories=memories,
                        available_actions=_AVAILABLE_ACTIONS,
                    )
                    if llm_resp.is_success and llm_resp.structured_data:
                        action = self._llm_to_proposed_action(
                            agent_id, llm_resp.structured_data, latest_snapshot
                        )
                    else:
                        # LLM call failed — fall back to heuristic for this tick
                        action = agent.evaluate_heuristic_action(
                            latest_snapshot, self.clock, self.environment
                        )
                else:
                    # ── HEURISTIC PATH (mock): pure-Python utility decision ────────────
                    action = agent.evaluate_heuristic_action(
                        latest_snapshot, self.clock, self.environment
                    )

                proposed_actions[agent_id] = action

            # 4. Step Simulation Engine
            snapshot = self.engine.step(proposed_actions)

            # 5. Process Social & Informational Outcomes from Action Logs
            recent_logs = self.engine.action_logs[-len(self.agents) :]
            for log in recent_logs:
                if log.status.value == "success":
                    act = log.action
                    if act.action_type == ActionType.SOCIALIZE and act.target_agent_id:
                        agent_a = self.agents[act.agent_id]
                        agent_b = self.agents.get(act.target_agent_id)
                        if agent_b:
                            rel_a = agent_a.get_or_create_relationship(act.target_agent_id)
                            rel_b = agent_b.get_or_create_relationship(act.agent_id)
                            rel_a.modify(
                                trust_delta=2.0, friendship_delta=3.0, current_tick=current_tick
                            )
                            rel_b.modify(
                                trust_delta=2.0, friendship_delta=3.0, current_tick=current_tick
                            )
                            self.social_graph.update_edge(
                                act.agent_id,
                                act.target_agent_id,
                                rel_a.trust,
                                rel_a.friendship,
                                rel_a.hostility,
                            )

                    elif act.action_type == ActionType.HELP_AGENT and act.target_agent_id:
                        agent_a = self.agents[act.agent_id]
                        agent_b = self.agents.get(act.target_agent_id)
                        if agent_b:
                            rel_b = agent_b.get_or_create_relationship(act.agent_id)
                            rel_b.modify(
                                trust_delta=15.0, friendship_delta=10.0, current_tick=current_tick
                            )
                            agent_b.memory.add_memory(
                                description=f"{agent_a.name} helped me with financial support (${act.amount:.2f}).",
                                importance=8,
                                tick=current_tick,
                                timestamp_str=snapshot.time_str,
                                emotional_valence=0.9,
                                involved_agent_ids=[agent_a.id],
                            )

            # 6. Compute Step Metrics & Telemetry
            stats = self.llm_provider.stats
            self.metrics_collector.compute_step_metrics(
                snapshot=snapshot,
                recent_actions=recent_logs,
                social_graph=self.social_graph,
                total_tokens=stats.total_prompt_tokens + stats.total_completion_tokens,
                total_cost=stats.total_cost_usd,
            )

        # 7. Post-Simulation Emergent Behavior Detection
        detected_patterns = EmergenceDetector.detect_all(
            current_tick=self.clock.current_tick,
            social_graph=self.social_graph,
            info_ledger=self.info_ledger,
            metrics_history=self.metrics_collector.history,
        )

        duration_sec = time.perf_counter() - t_start
        stats = self.llm_provider.stats

        return ExperimentResult(
            config=self.config,
            duration_seconds=round(duration_sec, 2),
            total_ticks=total_ticks,
            final_metrics=self.metrics_collector.history[-1]
            if self.metrics_collector.history
            else None,
            all_metrics=self.metrics_collector.history,
            detected_patterns=detected_patterns,
            total_tokens=stats.total_prompt_tokens + stats.total_completion_tokens,
            total_cost_usd=round(stats.total_cost_usd, 4),
            average_latency_ms=round(stats.average_latency_ms, 2),
            agent_summaries=[a.to_dict() for a in self.agents.values()],
        )
