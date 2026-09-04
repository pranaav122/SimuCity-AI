"""Unit tests for SimulationEngine and deterministic reproducibility."""

import pytest

from simucity.core.actions import ActionType, ProposedAction
from simucity.core.clock import SimulationClock
from simucity.core.engine import SimulationEngine
from simucity.core.environment import CampusEnvironment


def test_agent_registration(default_engine: SimulationEngine) -> None:
    state = default_engine.register_agent(
        agent_id="student_01",
        initial_location_id="dorm_north",
        initial_money=150.0,
    )
    assert state.agent_id == "student_01"
    assert state.location_id == "dorm_north"
    assert state.money == 150.0

    # Test duplicate registration error
    with pytest.raises(ValueError):
        default_engine.register_agent(agent_id="student_01")


def test_engine_single_step_eating(default_engine: SimulationEngine) -> None:
    # Register agent in cafeteria with initial hunger
    default_engine.register_agent(
        agent_id="hungry_student",
        initial_location_id="dining_hall",
        initial_money=50.0,
        initial_hunger=60.0,
        initial_energy=80.0,
    )

    action = ProposedAction(agent_id="hungry_student", action_type=ActionType.EAT)
    snap = default_engine.step({"hungry_student": action})

    agent_state = snap.agent_states["hungry_student"]
    # Meal costs $8, reduces hunger by 35 (plus 0.6 metabolism), adds 2 energy (minus 0.5 metabolism)
    assert agent_state.money == 42.0
    assert agent_state.hunger < 60.0
    assert default_engine.clock.current_tick == 1


def test_engine_movement_and_occupancy(default_engine: SimulationEngine) -> None:
    default_engine.register_agent("traveler", initial_location_id="dorm_north")
    assert "traveler" in default_engine.environment.get_location("dorm_north").occupants

    # Move to central library
    move_action = ProposedAction(
        agent_id="traveler",
        action_type=ActionType.MOVE,
        target_location_id="central_library",
    )
    snap = default_engine.step({"traveler": move_action})

    assert snap.agent_states["traveler"].location_id == "central_library"
    assert "traveler" in default_engine.environment.get_location("central_library").occupants
    assert "traveler" not in default_engine.environment.get_location("dorm_north").occupants


def test_engine_metabolism_passive_decay(default_engine: SimulationEngine) -> None:
    default_engine.register_agent(
        "idle_student",
        initial_location_id="dorm_north",
        initial_hunger=10.0,
        initial_energy=90.0,
        initial_social=50.0,
    )

    # 4 ticks of waiting (1 hour)
    for _ in range(4):
        default_engine.step(
            {"idle_student": ProposedAction(agent_id="idle_student", action_type=ActionType.WAIT)}
        )

    final_state = default_engine.agent_states["idle_student"]
    assert final_state.hunger > 10.0  # Hunger increased
    assert final_state.energy < 90.0  # Energy decayed
    assert final_state.social < 50.0  # Social isolation decay


def test_engine_deterministic_reproducibility() -> None:
    """Critical Research Verification: Assert identical state trajectories with same seed."""

    def run_simulation(seed_val: int):
        clock = SimulationClock(start_day=1, start_hour=8, start_minute=0)
        env = CampusEnvironment.create_default_campus()
        engine = SimulationEngine(seed=seed_val, environment=env, clock=clock)

        for i in range(10):
            engine.register_agent(
                agent_id=f"agent_{i:02d}",
                initial_location_id="dorm_north" if i % 2 == 0 else "dorm_south",
                initial_money=100.0 + (i * 10),
                initial_energy=80.0,
                initial_hunger=20.0,
            )

        # Run 40 ticks with a simple deterministic rule policy
        def rule_policy(snapshot, agent_id):
            agent = snapshot.agent_states[agent_id]
            if agent.hunger > 50:
                if agent.location_id != "dining_hall":
                    return ProposedAction(
                        agent_id=agent_id,
                        action_type=ActionType.MOVE,
                        target_location_id="dining_hall",
                    )
                return ProposedAction(agent_id=agent_id, action_type=ActionType.EAT)
            elif agent.energy < 30:
                if agent.location_id != "dorm_north":
                    return ProposedAction(
                        agent_id=agent_id,
                        action_type=ActionType.MOVE,
                        target_location_id="dorm_north",
                    )
                return ProposedAction(agent_id=agent_id, action_type=ActionType.SLEEP)
            else:
                if agent.location_id != "classroom_hall":
                    return ProposedAction(
                        agent_id=agent_id,
                        action_type=ActionType.MOVE,
                        target_location_id="classroom_hall",
                    )
                return ProposedAction(agent_id=agent_id, action_type=ActionType.ATTEND_CLASS)

        snapshots = engine.run_ticks(40, policy_fn=rule_policy)
        return snapshots, engine.action_logs

    # Run 1 with Seed 42
    snaps_1, logs_1 = run_simulation(42)

    # Run 2 with Seed 42
    snaps_2, logs_2 = run_simulation(42)

    # Verify bit-for-bit equivalence across all 40 ticks
    assert len(snaps_1) == len(snaps_2) == 40
    assert len(logs_1) == len(logs_2)

    for tick_idx in range(40):
        s1 = snaps_1[tick_idx]
        s2 = snaps_2[tick_idx]
        assert s1.tick == s2.tick
        assert s1.time_str == s2.time_str
        assert s1.location_occupancies == s2.location_occupancies

        for agent_id in s1.agent_states:
            a1 = s1.agent_states[agent_id]
            a2 = s2.agent_states[agent_id]
            assert a1.location_id == a2.location_id
            assert a1.money == a2.money
            assert pytest.approx(a1.energy, 1e-5) == a2.energy
            assert pytest.approx(a1.hunger, 1e-5) == a2.hunger
            assert pytest.approx(a1.stress, 1e-5) == a2.stress
            assert pytest.approx(a1.knowledge, 1e-5) == a2.knowledge


def test_engine_work_and_study_actions(default_engine: SimulationEngine) -> None:
    # 1. Work at campus store
    default_engine.register_agent(
        "worker_bob", initial_location_id="campus_store", initial_money=20.0, initial_energy=80.0
    )
    work_action = ProposedAction(agent_id="worker_bob", action_type=ActionType.WORK)
    snap = default_engine.step({"worker_bob": work_action})

    bob_state = snap.agent_states["worker_bob"]
    # Earned $15 wage -> $35
    assert bob_state.money == 35.0
    assert bob_state.current_activity == "working"

    # 2. Study at central library
    default_engine.register_agent(
        "scholar_alice",
        initial_location_id="central_library",
        initial_knowledge=10.0,
        initial_energy=80.0,
    )
    study_action = ProposedAction(agent_id="scholar_alice", action_type=ActionType.STUDY)
    snap2 = default_engine.step({"scholar_alice": study_action})

    alice_state = snap2.agent_states["scholar_alice"]
    assert alice_state.knowledge > 10.0
    assert alice_state.current_activity == "studying"


def test_engine_help_agent_resource_transfer(default_engine: SimulationEngine) -> None:
    default_engine.register_agent("giver", initial_location_id="dining_hall", initial_money=100.0)
    default_engine.register_agent("receiver", initial_location_id="dining_hall", initial_money=10.0)

    help_action = ProposedAction(
        agent_id="giver",
        action_type=ActionType.HELP_AGENT,
        target_agent_id="receiver",
        amount=25.0,
    )
    snap = default_engine.step({"giver": help_action})

    giver_state = snap.agent_states["giver"]
    receiver_state = snap.agent_states["receiver"]

    assert giver_state.money == 75.0
    assert receiver_state.money == 35.0


def test_engine_events_and_price_multipliers(default_engine: SimulationEngine) -> None:
    default_engine.set_price_multiplier("dining_hall", 1.5)
    default_engine.add_event("inflation_surge")

    assert "inflation_surge" in default_engine.active_events
    assert default_engine.price_multipliers["dining_hall"] == 1.5

    default_engine.register_agent(
        "diner", initial_location_id="dining_hall", initial_money=50.0, initial_hunger=50.0
    )
    eat_action = ProposedAction(agent_id="diner", action_type=ActionType.EAT)
    snap = default_engine.step({"diner": eat_action})

    # Base price $8 * 1.5 = $12 deducted
    assert snap.agent_states["diner"].money == 38.0
    assert "inflation_surge" in snap.active_event_ids

    default_engine.remove_event("inflation_surge")
    assert "inflation_surge" not in default_engine.active_events
