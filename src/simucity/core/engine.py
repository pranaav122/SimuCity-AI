"""Deterministic Simulation Engine and Action Validation System."""

from collections.abc import Callable

from simucity.core.actions import ActionResult, ActionStatus, ActionType, ProposedAction
from simucity.core.clock import SimulationClock
from simucity.core.environment import CampusEnvironment, LocationAffordance
from simucity.core.world_state import AgentStateSnapshot, WorldStateSnapshot
from simucity.utils.rng import SeededRNG


class ActionValidator:
    """Validates physical and environmental constraints for proposed agent actions."""

    @staticmethod
    def validate(
        action: ProposedAction,
        agent_state: AgentStateSnapshot,
        environment: CampusEnvironment,
        clock: SimulationClock,
        price_multipliers: dict[str, float],
    ) -> tuple[bool, ActionStatus, str | None]:
        """Validate if a proposed action is physically possible.

        Returns (is_valid, status, reason).
        """
        curr_loc_id = agent_state.location_id
        if curr_loc_id not in environment.locations:
            return (
                False,
                ActionStatus.FAILED_PREREQUISITE,
                f"Current location '{curr_loc_id}' is invalid.",
            )

        curr_loc = environment.get_location(curr_loc_id)
        current_hour = clock.hour

        # 1. Movement Action
        if action.action_type == ActionType.MOVE:
            target_id = action.target_location_id
            if not target_id or target_id not in environment.locations:
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    f"Target location '{target_id}' does not exist.",
                )
            if target_id == curr_loc_id:
                return False, ActionStatus.REJECTED, "Agent is already at the target location."
            target_loc = environment.get_location(target_id)
            if not target_loc.is_open(current_hour):
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    f"Location '{target_loc.name}' is closed at {clock.time_str}.",
                )
            if not target_loc.has_capacity:
                return (
                    False,
                    ActionStatus.CONFLICT,
                    f"Location '{target_loc.name}' is at full capacity ({target_loc.capacity}).",
                )
            return True, ActionStatus.SUCCESS, None

        # 2. Wait / Idle
        if action.action_type == ActionType.WAIT:
            return True, ActionStatus.SUCCESS, None

        # 3. Sleep
        if action.action_type == ActionType.SLEEP:
            if not curr_loc.allows(LocationAffordance.SLEEP):
                return (
                    False,
                    ActionStatus.REJECTED,
                    f"Cannot sleep in '{curr_loc.name}'. Requires dormitory.",
                )
            return True, ActionStatus.SUCCESS, None

        # 4. Rest
        if action.action_type == ActionType.REST:
            if not curr_loc.allows(LocationAffordance.REST):
                return False, ActionStatus.REJECTED, f"Cannot rest in '{curr_loc.name}'."
            return True, ActionStatus.SUCCESS, None

        # 5. Eat
        if action.action_type == ActionType.EAT:
            if not curr_loc.allows(LocationAffordance.EAT):
                return False, ActionStatus.REJECTED, f"No food available in '{curr_loc.name}'."
            effective_cost = curr_loc.base_cost * price_multipliers.get(curr_loc.id, 1.0)
            if agent_state.money < effective_cost:
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    f"Insufficient funds for meal. Cost: ${effective_cost:.2f}, Agent balance: ${agent_state.money:.2f}",
                )
            return True, ActionStatus.SUCCESS, None

        # 6. Study
        if action.action_type == ActionType.STUDY:
            if not curr_loc.allows(LocationAffordance.STUDY):
                return (
                    False,
                    ActionStatus.REJECTED,
                    f"Cannot study effectively in '{curr_loc.name}'.",
                )
            if agent_state.energy < 5.0:
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    "Agent is too exhausted to study (energy < 5).",
                )
            return True, ActionStatus.SUCCESS, None

        # 7. Attend Class
        if action.action_type == ActionType.ATTEND_CLASS:
            if not curr_loc.allows(LocationAffordance.ATTEND_CLASS):
                return False, ActionStatus.REJECTED, f"No classes held in '{curr_loc.name}'."
            if not clock.is_class_hours:
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    f"Classes are not in session at {clock.time_str}.",
                )
            if agent_state.energy < 5.0:
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    "Agent is too exhausted to attend class.",
                )
            return True, ActionStatus.SUCCESS, None

        # 8. Work (Earn money)
        if action.action_type == ActionType.WORK:
            if not curr_loc.allows(LocationAffordance.WORK):
                return (
                    False,
                    ActionStatus.REJECTED,
                    f"No work shifts available in '{curr_loc.name}'.",
                )
            if not curr_loc.is_open(current_hour):
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    f"Location '{curr_loc.name}' is closed.",
                )
            if agent_state.energy < 10.0:
                return False, ActionStatus.FAILED_PREREQUISITE, "Agent is too exhausted to work."
            return True, ActionStatus.SUCCESS, None

        # 9. Purchase Item
        if action.action_type == ActionType.PURCHASE_ITEM:
            if not curr_loc.allows(LocationAffordance.PURCHASE):
                return (
                    False,
                    ActionStatus.REJECTED,
                    f"No purchasing facilities in '{curr_loc.name}'.",
                )
            item_cost = (
                action.amount
                if action.amount > 0
                else (curr_loc.base_cost * price_multipliers.get(curr_loc.id, 1.0))
            )
            if agent_state.money < item_cost:
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    f"Insufficient funds. Required: ${item_cost:.2f}, Balance: ${agent_state.money:.2f}",
                )
            return True, ActionStatus.SUCCESS, None

        # 10. Socialize
        if action.action_type == ActionType.SOCIALIZE:
            if not curr_loc.allows(LocationAffordance.SOCIALIZE):
                return (
                    False,
                    ActionStatus.REJECTED,
                    f"Socializing is restricted in '{curr_loc.name}' (quiet area).",
                )
            if action.target_agent_id:
                # Target must be co-located
                target_loc_id = environment.get_agent_location_id(action.target_agent_id)
                if target_loc_id != curr_loc_id:
                    return (
                        False,
                        ActionStatus.FAILED_PREREQUISITE,
                        f"Target agent '{action.target_agent_id}' is not in the same location.",
                    )
            return True, ActionStatus.SUCCESS, None

        # 11. Help Agent
        if action.action_type == ActionType.HELP_AGENT:
            if not action.target_agent_id:
                return False, ActionStatus.REJECTED, "Help action requires a target agent."
            target_loc_id = environment.get_agent_location_id(action.target_agent_id)
            if target_loc_id != curr_loc_id:
                return False, ActionStatus.FAILED_PREREQUISITE, "Target agent is not co-located."
            if action.amount > 0 and agent_state.money < action.amount:
                return False, ActionStatus.FAILED_PREREQUISITE, "Insufficient funds to transfer."
            return True, ActionStatus.SUCCESS, None

        # 12. Share Information
        if action.action_type == ActionType.SHARE_INFO:
            if not action.target_agent_id:
                return False, ActionStatus.REJECTED, "Share info requires a target agent."
            target_loc_id = environment.get_agent_location_id(action.target_agent_id)
            if target_loc_id != curr_loc_id:
                return (
                    False,
                    ActionStatus.FAILED_PREREQUISITE,
                    "Target agent is not co-located to receive info.",
                )
            return True, ActionStatus.SUCCESS, None

        return True, ActionStatus.SUCCESS, None


class SimulationEngine:
    """Core deterministic simulation orchestrator."""

    def __init__(
        self,
        seed: int = 42,
        environment: CampusEnvironment | None = None,
        clock: SimulationClock | None = None,
    ) -> None:
        self.seed = seed
        self.rng = SeededRNG(seed)
        self.clock = clock or SimulationClock()
        self.environment = environment or CampusEnvironment.create_default_campus()
        self.agent_states: dict[str, AgentStateSnapshot] = {}
        self.price_multipliers: dict[str, float] = {}
        self.active_events: list[str] = []
        self.history: list[WorldStateSnapshot] = []
        self.action_logs: list[ActionResult] = []

    def register_agent(
        self,
        agent_id: str,
        initial_location_id: str = "dorm_north",
        initial_money: float = 100.0,
        initial_energy: float = 100.0,
        initial_hunger: float = 0.0,
        initial_stress: float = 0.0,
        initial_social: float = 50.0,
        initial_knowledge: float = 10.0,
        initial_gpa: float = 3.5,
    ) -> AgentStateSnapshot:
        """Registers a new agent into the environment and world state."""
        if agent_id in self.agent_states:
            raise ValueError(f"Agent '{agent_id}' is already registered.")

        if initial_location_id not in self.environment.locations:
            raise KeyError(f"Location '{initial_location_id}' does not exist in environment.")

        success = self.environment.move_agent(agent_id, None, initial_location_id)
        if not success:
            raise RuntimeError(
                f"Could not place agent in '{initial_location_id}': capacity exceeded."
            )

        state = AgentStateSnapshot(
            agent_id=agent_id,
            location_id=initial_location_id,
            money=initial_money,
            energy=initial_energy,
            hunger=initial_hunger,
            stress=initial_stress,
            social=initial_social,
            knowledge=initial_knowledge,
            gpa=initial_gpa,
            current_activity="idle",
        )
        self.agent_states[agent_id] = state
        return state

    def set_price_multiplier(self, location_id: str, multiplier: float) -> None:
        """Sets price inflation or discount for a location."""
        self.price_multipliers[location_id] = max(0.0, multiplier)

    def add_event(self, event_id: str) -> None:
        if event_id not in self.active_events:
            self.active_events.append(event_id)

    def remove_event(self, event_id: str) -> None:
        if event_id in self.active_events:
            self.active_events.remove(event_id)

    def step(self, proposed_actions: dict[str, ProposedAction] | None = None) -> WorldStateSnapshot:
        """Executes a single discrete simulation tick."""
        proposed = proposed_actions or {}
        tick = self.clock.current_tick

        # Sort agent IDs alphabetically to ensure strictly deterministic resolution order
        sorted_agent_ids = sorted(self.agent_states.keys())

        # 1. Process Actions for each agent
        for agent_id in sorted_agent_ids:
            state = self.agent_states[agent_id]
            action = proposed.get(
                agent_id,
                ProposedAction(agent_id=agent_id, action_type=ActionType.WAIT),
            )

            # Validate Action
            is_valid, status, reason = ActionValidator.validate(
                action=action,
                agent_state=state,
                environment=self.environment,
                clock=self.clock,
                price_multipliers=self.price_multipliers,
            )

            result = ActionResult(
                action=action,
                status=status,
                reason=reason,
                tick=tick,
            )

            if not is_valid:
                # Fallback to WAIT if proposed action is invalid
                state.current_activity = "idle"
                self.action_logs.append(result)
                continue

            # Execute Valid Action
            curr_loc = self.environment.get_location(state.location_id)
            effective_price_mult = self.price_multipliers.get(state.location_id, 1.0)

            if action.action_type == ActionType.MOVE:
                target_loc_id = action.target_location_id
                assert target_loc_id is not None
                moved = self.environment.move_agent(agent_id, state.location_id, target_loc_id)
                if moved:
                    state.location_id = target_loc_id
                    state.current_activity = f"traveling_to_{target_loc_id}"
                    result.location_changed_to = target_loc_id
                    result.energy_delta = -1.0
                else:
                    result.status = ActionStatus.CONFLICT
                    result.reason = "Target location capacity filled during simultaneous step."

            elif action.action_type == ActionType.SLEEP:
                # Sleep recovers 8 energy per tick, decreases stress by 2
                result.energy_delta = 8.0
                result.stress_delta = -2.0
                state.current_activity = "sleeping"

            elif action.action_type == ActionType.REST:
                result.energy_delta = 3.0
                result.stress_delta = -1.0
                state.current_activity = "resting"

            elif action.action_type == ActionType.EAT:
                meal_cost = curr_loc.base_cost * effective_price_mult
                result.money_delta = -meal_cost
                result.hunger_delta = -35.0  # Significantly relieves hunger
                result.energy_delta = 2.0
                state.current_activity = "eating"

            elif action.action_type == ActionType.STUDY:
                # Noise penalty
                noise = curr_loc.effective_noise()
                knowledge_gain = max(0.2, 1.0 - (noise * 0.5))
                result.knowledge_delta = knowledge_gain
                result.energy_delta = -2.5
                result.stress_delta = 1.0
                state.current_activity = "studying"

            elif action.action_type == ActionType.ATTEND_CLASS:
                result.knowledge_delta = 2.0
                result.energy_delta = -3.0
                result.stress_delta = 1.5
                result.social_delta = 0.5
                state.current_activity = "attending_class"

            elif action.action_type == ActionType.WORK:
                wage = 15.0  # $15 earned per tick of work
                result.money_delta = wage
                result.energy_delta = -4.0
                result.stress_delta = 2.0
                state.current_activity = "working"

            elif action.action_type == ActionType.PURCHASE_ITEM:
                cost = (
                    action.amount
                    if action.amount > 0
                    else (curr_loc.base_cost * effective_price_mult)
                )
                result.money_delta = -cost
                result.social_delta = 1.0
                state.current_activity = "shopping"

            elif action.action_type == ActionType.SOCIALIZE:
                result.social_delta = 4.0
                result.stress_delta = -2.0
                result.energy_delta = -1.0
                state.current_activity = "socializing"

            elif action.action_type == ActionType.HELP_AGENT:
                if action.amount > 0:
                    result.money_delta = -action.amount
                    # Add to recipient if registered
                    if action.target_agent_id in self.agent_states:
                        self.agent_states[action.target_agent_id].money += action.amount
                result.social_delta = 5.0
                result.energy_delta = -2.0
                state.current_activity = f"helping_{action.target_agent_id}"

            elif action.action_type == ActionType.SHARE_INFO:
                result.social_delta = 2.0
                state.current_activity = f"sharing_info_with_{action.target_agent_id}"

            elif action.action_type == ActionType.WAIT:
                state.current_activity = "idle"

            # Apply deltas to agent state with boundary clamping
            state.energy = max(0.0, min(100.0, state.energy + result.energy_delta))
            state.hunger = max(0.0, min(100.0, state.hunger + result.hunger_delta))
            state.stress = max(0.0, min(100.0, state.stress + result.stress_delta))
            state.social = max(0.0, min(100.0, state.social + result.social_delta))
            state.knowledge = max(0.0, min(100.0, state.knowledge + result.knowledge_delta))
            state.money = max(0.0, state.money + result.money_delta)

            # Update GPA slightly based on knowledge level
            state.gpa = min(4.0, max(1.0, 2.0 + (state.knowledge / 50.0)))

            self.action_logs.append(result)

        # 2. Passive Natural Decay / Metabolism (per tick)
        for agent_id in sorted_agent_ids:
            state = self.agent_states[agent_id]
            # Hunger naturally builds up: +0.6 per 15-min tick (approx +57 per 24h)
            state.hunger = min(100.0, state.hunger + 0.6)
            # Energy naturally decays when awake: -0.5 per tick
            if state.current_activity != "sleeping":
                state.energy = max(0.0, state.energy - 0.5)

            # High hunger / extreme exhaustion causes stress escalation
            if state.hunger > 75.0:
                state.stress = min(100.0, state.stress + 1.0)
            if state.energy < 15.0:
                state.stress = min(100.0, state.stress + 1.0)

            # Social isolation decay: -0.2 per tick
            state.social = max(0.0, state.social - 0.2)

        # 3. Create Immutable Snapshot
        occupancies = {
            loc_id: sorted(list(loc.occupants))
            for loc_id, loc in self.environment.locations.items()
        }
        snapshot = WorldStateSnapshot(
            tick=tick,
            day=self.clock.day,
            hour=self.clock.hour,
            minute=self.clock.minute,
            time_str=self.clock.time_str,
            day_of_week=self.clock.day_of_week,
            weather="Clear",
            campus_alert_level="Normal",
            location_occupancies=occupancies,
            price_multipliers=dict(self.price_multipliers),
            active_event_ids=list(self.active_events),
            agent_states={k: v.model_copy() for k, v in self.agent_states.items()},
        )
        self.history.append(snapshot)

        # 4. Advance Clock
        self.clock.advance(1)

        return snapshot

    def run_ticks(
        self,
        n_ticks: int,
        policy_fn: Callable[[WorldStateSnapshot, str], ProposedAction] | None = None,
    ) -> list[WorldStateSnapshot]:
        """Runs the simulation for a given number of ticks with an optional decision policy."""
        snapshots = []
        for _ in range(n_ticks):
            proposed_actions: dict[str, ProposedAction] = {}
            if policy_fn:
                latest_snapshot = self.history[-1] if self.history else None
                for agent_id in self.agent_states.keys():
                    if latest_snapshot:
                        action = policy_fn(latest_snapshot, agent_id)
                        proposed_actions[agent_id] = action
            snap = self.step(proposed_actions)
            snapshots.append(snap)
        return snapshots
