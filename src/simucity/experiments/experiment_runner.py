"""Reproducible experiment framework, batch comparison runner, and telemetry exporter."""

import time
from typing import Any, Dict, List, Optional
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
from simucity.llm.claude_provider import ClaudeProvider
from simucity.llm.gemini_provider import GeminiProvider
from simucity.llm.mock_provider import MockLLMProvider
from simucity.llm.provider import LLMProvider
from simucity.metrics.emergence import EmergenceDetector, EmergentPattern
from simucity.metrics.metrics_collector import MetricsCollector, SimulationMetrics
from simucity.social.social_network import SocialGraph
from simucity.utils.rng import SeededRNG


class ExperimentConfig(BaseModel):
    """Declarative specification of a reproducible simulation experiment."""

    experiment_id: str
    name: str = "Campus Emergence Study"
    number_of_agents: int = Field(default=16, ge=2, le=200)
    simulation_days: int = Field(default=3, ge=1, le=60)
    model: str = Field(default="mock", description="'claude' | 'gemini' | 'mock'")
    event_scenario: Optional[str] = Field(default=None, description="Preset shock event ID")
    seed: int = Field(default=42, description="RNG seed for deterministic reproducibility")


class ExperimentResult(BaseModel):
    """Complete summary outcome of an experiment run."""

    config: ExperimentConfig
    duration_seconds: float
    total_ticks: int
    final_metrics: Optional[SimulationMetrics] = None
    all_metrics: List[SimulationMetrics] = Field(default_factory=list)
    detected_patterns: List[EmergentPattern] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    average_latency_ms: float = 0.0
    agent_summaries: List[Dict[str, Any]] = Field(default_factory=list)


class ExperimentRunner:
    """Orchestrates multi-agent simulation experiments with strict reproducibility."""

    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config
        self.rng = SeededRNG(config.seed)
        self.clock = SimulationClock(start_day=1, start_hour=8, start_minute=0)
        self.environment = CampusEnvironment.create_default_campus()
        self.engine = SimulationEngine(seed=config.seed, environment=self.environment, clock=self.clock)
        self.agents: Dict[str, SimuAgent] = {}
        self.social_graph = SocialGraph()
        self.info_ledger = InformationLedger()
        self.event_manager = EventManager()
        self.metrics_collector = MetricsCollector()

        # Instantiate LLM Provider
        if config.model == "claude":
            self.llm_provider: LLMProvider = ClaudeProvider()
        elif config.model == "gemini":
            self.llm_provider = GeminiProvider()
        else:
            self.llm_provider = MockLLMProvider()

        self._setup_population()
        self._setup_events()

    def _setup_population(self) -> None:
        """Instantiates heterogeneous population with diverse personalities and goals."""
        archetypes = ["scholar", "socialite", "entrepreneur", "balanced"]
        names = [
            "Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah",
            "Ian", "Julia", "Kevin", "Luna", "Marcus", "Nora", "Oliver", "Piper",
            "Quinn", "Riley", "Sam", "Tara", "Umar", "Violet", "Will", "Xena"
        ]

        for i in range(self.config.number_of_agents):
            agent_id = f"agent_{i+1:02d}"
            name = names[i % len(names)] if i < len(names) else f"Student_{i+1}"
            archetype = archetypes[i % len(archetypes)]

            # Generate personality with controlled stochastic perturbation around archetype
            if archetype == "scholar":
                p = Personality.scholarly_introvert()
            elif archetype == "socialite":
                p = Personality.social_butterfly()
            elif archetype == "entrepreneur":
                p = Personality.ambitious_entrepreneur()
            else:
                p = Personality.thrifty_slacker()

            # Slight seeded jitter
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
            self.event_manager.schedule_event(SimulationEvent.cafeteria_price_shock(trigger_tick=96))
        elif self.config.event_scenario == "surprise_midterm":
            self.event_manager.schedule_event(SimulationEvent.surprise_midterm_exam(trigger_tick=96))
        elif self.config.event_scenario == "transit_strike":
            self.event_manager.schedule_event(SimulationEvent.transit_strike(trigger_tick=96))

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
            proposed_actions: Dict[str, ProposedAction] = {}
            for agent_id, agent in self.agents.items():
                if latest_snapshot:
                    action = agent.evaluate_heuristic_action(latest_snapshot, self.clock, self.environment)
                else:
                    action = ProposedAction(agent_id=agent_id, action_type=ActionType.WAIT)
                proposed_actions[agent_id] = action

            # 4. Step Simulation Engine
            snapshot = self.engine.step(proposed_actions)

            # 5. Process Social & Informational Outcomes from Action Logs
            recent_logs = self.engine.action_logs[-len(self.agents):]
            for log in recent_logs:
                if log.status.value == "success":
                    act = log.action
                    if act.action_type == ActionType.SOCIALIZE and act.target_agent_id:
                        agent_a = self.agents[act.agent_id]
                        agent_b = self.agents.get(act.target_agent_id)
                        if agent_b:
                            rel_a = agent_a.get_or_create_relationship(act.target_agent_id)
                            rel_b = agent_b.get_or_create_relationship(act.agent_id)
                            rel_a.modify(trust_delta=2.0, friendship_delta=3.0, current_tick=current_tick)
                            rel_b.modify(trust_delta=2.0, friendship_delta=3.0, current_tick=current_tick)
                            self.social_graph.update_edge(
                                act.agent_id, act.target_agent_id, rel_a.trust, rel_a.friendship, rel_a.hostility
                            )

                    elif act.action_type == ActionType.HELP_AGENT and act.target_agent_id:
                        agent_a = self.agents[act.agent_id]
                        agent_b = self.agents.get(act.target_agent_id)
                        if agent_b:
                            rel_b = agent_b.get_or_create_relationship(act.agent_id)
                            rel_b.modify(trust_delta=15.0, friendship_delta=10.0, current_tick=current_tick)
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

        result = ExperimentResult(
            config=self.config,
            duration_seconds=round(duration_sec, 2),
            total_ticks=total_ticks,
            final_metrics=self.metrics_collector.history[-1] if self.metrics_collector.history else None,
            all_metrics=self.metrics_collector.history,
            detected_patterns=detected_patterns,
            total_tokens=stats.total_prompt_tokens + stats.total_completion_tokens,
            total_cost_usd=round(stats.total_cost_usd, 4),
            average_latency_ms=round(stats.average_latency_ms, 2),
            agent_summaries=[a.to_dict() for a in self.agents.values()],
        )
        return result
