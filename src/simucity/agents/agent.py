"""Autonomous SimuAgent cognitive core and decision pipeline."""

from typing import Any

from simucity.agents.goals import AgentGoal, create_default_goals
from simucity.agents.needs import AgentNeeds
from simucity.agents.personality import Personality
from simucity.core.actions import ActionType, ProposedAction
from simucity.core.clock import SimulationClock
from simucity.core.environment import CampusEnvironment, LocationAffordance
from simucity.core.world_state import WorldStateSnapshot
from simucity.memory.memory_stream import MemoryStream
from simucity.social.relationship import Relationship


class SimuAgent:
    """Full cognitive autonomous agent in the SimuCity simulation."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        age: int = 20,
        personality: Personality | None = None,
        needs: AgentNeeds | None = None,
        goals: list[AgentGoal] | None = None,
        archetype: str = "balanced",
    ) -> None:
        self.id = agent_id
        self.name = name
        self.age = age
        self.personality = personality or Personality()
        self.needs = needs or AgentNeeds()
        self.goals = goals or create_default_goals(archetype)
        self.memory = MemoryStream()
        self.relationships: dict[str, Relationship] = {}
        self.known_info_ids: set[str] = set()
        self.current_plan: str = "Attend morning classes, study in library, socialize in cafeteria."

    def get_or_create_relationship(self, target_agent_id: str) -> Relationship:
        if target_agent_id not in self.relationships:
            # Baseline initial trust influenced by personality.trust
            base_trust = (self.personality.trust * 20.0) - 10.0  # -10 to +10
            self.relationships[target_agent_id] = Relationship(
                target_agent_id=target_agent_id,
                trust=base_trust,
            )
        return self.relationships[target_agent_id]

    def sync_from_snapshot(self, snapshot: WorldStateSnapshot) -> None:
        """Syncs homeostatic needs from the deterministic world state snapshot."""
        if self.id in snapshot.agent_states:
            state = snapshot.agent_states[self.id]
            self.needs.hunger = state.hunger
            self.needs.energy = state.energy
            self.needs.stress = state.stress
            self.needs.social = state.social
            self.needs.knowledge = state.knowledge

            # Update goal progress
            for goal in self.goals:
                if goal.id == "g_gpa":
                    goal.update_progress(state.gpa)
                elif goal.id == "g_wealth" or goal.id == "g_budget":
                    goal.update_progress(state.money)
                elif goal.id == "g_friends":
                    friend_count = sum(1 for r in self.relationships.values() if r.friendship > 20)
                    goal.update_progress(float(friend_count))

    def evaluate_heuristic_action(
        self,
        world_state: WorldStateSnapshot,
        clock: SimulationClock,
        environment: CampusEnvironment,
    ) -> ProposedAction:
        """High-performance utility-based action policy balancing personality, homeostatic drives, and goals."""
        curr_loc_id = (
            world_state.agent_states[self.id].location_id
            if self.id in world_state.agent_states
            else "dorm_north"
        )
        curr_loc = environment.get_location(curr_loc_id)
        current_money = (
            world_state.agent_states[self.id].money
            if self.id in world_state.agent_states
            else 100.0
        )

        # 1. Critical Physiological Priority: Extreme Hunger (>= 70)
        if self.needs.hunger >= 65.0 and current_money >= 4.0:
            if curr_loc.allows(LocationAffordance.EAT):
                return ProposedAction(agent_id=self.id, action_type=ActionType.EAT)
            return ProposedAction(
                agent_id=self.id, action_type=ActionType.MOVE, target_location_id="dining_hall"
            )

        # 2. Critical Physiological Priority: Severe Exhaustion (Energy <= 20) or Nighttime
        if self.needs.energy <= 20.0 or (clock.is_night and self.needs.energy <= 60.0):
            if curr_loc.allows(LocationAffordance.SLEEP):
                return ProposedAction(agent_id=self.id, action_type=ActionType.SLEEP)
            # Find nearest dorm
            return ProposedAction(
                agent_id=self.id, action_type=ActionType.MOVE, target_location_id="dorm_north"
            )

        # 3. High Academic Schedule Priority: Mon-Fri Class Hours (08:00 - 16:00)
        if clock.is_class_hours and self.needs.energy >= 25.0:
            if curr_loc.allows(LocationAffordance.ATTEND_CLASS):
                return ProposedAction(agent_id=self.id, action_type=ActionType.ATTEND_CLASS)
            return ProposedAction(
                agent_id=self.id, action_type=ActionType.MOVE, target_location_id="classroom_hall"
            )

        # 4. Solvency / Work Priority: Very Low Money (< $15)
        if current_money < 15.0 and self.needs.energy >= 20.0:
            if curr_loc.allows(LocationAffordance.WORK) and curr_loc.is_open(clock.hour):
                return ProposedAction(agent_id=self.id, action_type=ActionType.WORK)
            return ProposedAction(
                agent_id=self.id, action_type=ActionType.MOVE, target_location_id="campus_store"
            )

        # 5. Stress Relief: High Stress (>= 60)
        if self.needs.stress >= 60.0:
            if curr_loc.allows(LocationAffordance.REST) or curr_loc.allows(
                LocationAffordance.EXERCISE
            ):
                return ProposedAction(agent_id=self.id, action_type=ActionType.REST)
            return ProposedAction(
                agent_id=self.id, action_type=ActionType.MOVE, target_location_id="rec_center"
            )

        # 6. Social Drive: High Extroversion or Low Social Level (<= 40)
        co_located_peers = environment.get_co_located_agents(self.id)
        if (self.needs.social <= 40.0 or self.personality.extroversion >= 0.7) and co_located_peers:
            if curr_loc.allows(LocationAffordance.SOCIALIZE):
                target_peer = co_located_peers[0]
                # High cooperation agents occasionally help struggling friends
                if self.personality.cooperation >= 0.7 and current_money > 50.0:
                    peer_rel = self.get_or_create_relationship(target_peer)
                    if peer_rel.friendship > 10.0:
                        return ProposedAction(
                            agent_id=self.id,
                            action_type=ActionType.HELP_AGENT,
                            target_agent_id=target_peer,
                            amount=10.0,
                        )
                return ProposedAction(
                    agent_id=self.id,
                    action_type=ActionType.SOCIALIZE,
                    target_agent_id=target_peer,
                )

        # 7. Academic Ambition Study Priority
        if self.personality.ambition >= 0.6 and self.needs.energy >= 30.0:
            if curr_loc.allows(LocationAffordance.STUDY):
                return ProposedAction(agent_id=self.id, action_type=ActionType.STUDY)
            return ProposedAction(
                agent_id=self.id, action_type=ActionType.MOVE, target_location_id="central_library"
            )

        # 8. Default fallback: Rest or Wait
        if curr_loc.allows(LocationAffordance.REST):
            return ProposedAction(agent_id=self.id, action_type=ActionType.REST)
        return ProposedAction(agent_id=self.id, action_type=ActionType.WAIT)

    def to_dict(self) -> dict[str, Any]:
        """Serializes full cognitive agent state for REST endpoints and inspection."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "personality": self.personality.to_dict(),
            "needs": self.needs.model_dump(),
            "goals": [g.model_dump() for g in self.goals],
            "relationships": {k: v.model_dump() for k, v in self.relationships.items()},
            "current_plan": self.current_plan,
            "recent_memories": [m.model_dump() for m in self.memory.short_term_buffer[-5:]],
        }
