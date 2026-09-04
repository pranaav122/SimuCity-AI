"""Unit tests for ActionValidator and action constraints."""

from simucity.core.actions import ActionStatus, ActionType, ProposedAction
from simucity.core.clock import SimulationClock
from simucity.core.engine import ActionValidator
from simucity.core.environment import CampusEnvironment
from simucity.core.world_state import AgentStateSnapshot


def test_action_validator_valid_move(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    state = AgentStateSnapshot(agent_id="agent_1", location_id="dorm_north")
    default_campus.move_agent("agent_1", None, "dorm_north")

    action = ProposedAction(
        agent_id="agent_1",
        action_type=ActionType.MOVE,
        target_location_id="dining_hall",
    )
    is_valid, status, reason = ActionValidator.validate(
        action, state, default_campus, default_clock, {}
    )
    assert is_valid
    assert status == ActionStatus.SUCCESS
    assert reason is None


def test_action_validator_invalid_sleep_in_classroom(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    state = AgentStateSnapshot(agent_id="agent_1", location_id="classroom_hall")
    default_campus.move_agent("agent_1", None, "classroom_hall")

    action = ProposedAction(agent_id="agent_1", action_type=ActionType.SLEEP)
    is_valid, status, reason = ActionValidator.validate(
        action, state, default_campus, default_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.REJECTED
    assert "dormitory" in reason.lower()


def test_action_validator_insufficient_funds_for_meal(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    # Dining hall meal base cost is $8.0
    state = AgentStateSnapshot(agent_id="broke_agent", location_id="dining_hall", money=3.0)
    default_campus.move_agent("broke_agent", None, "dining_hall")

    action = ProposedAction(agent_id="broke_agent", action_type=ActionType.EAT)
    is_valid, status, reason = ActionValidator.validate(
        action, state, default_campus, default_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.FAILED_PREREQUISITE
    assert "insufficient funds" in reason.lower()


def test_action_validator_attend_class_out_of_hours(default_campus: CampusEnvironment) -> None:
    # Clock at 21:00 (outside class hours 08:00 - 17:00)
    night_clock = SimulationClock(start_hour=21, start_minute=0)
    state = AgentStateSnapshot(agent_id="student_1", location_id="classroom_hall")
    default_campus.move_agent("student_1", None, "classroom_hall")

    action = ProposedAction(agent_id="student_1", action_type=ActionType.ATTEND_CLASS)
    is_valid, status, reason = ActionValidator.validate(
        action, state, default_campus, night_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.FAILED_PREREQUISITE
    assert "not in session" in reason.lower()


def test_action_validator_socialize_not_co_located(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    default_campus.move_agent("alice", None, "dorm_north")
    default_campus.move_agent("bob", None, "central_library")
    state_alice = AgentStateSnapshot(agent_id="alice", location_id="dorm_north")

    action = ProposedAction(
        agent_id="alice",
        action_type=ActionType.SOCIALIZE,
        target_agent_id="bob",
    )
    is_valid, status, reason = ActionValidator.validate(
        action, state_alice, default_campus, default_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.FAILED_PREREQUISITE
    assert "not in the same location" in reason.lower()


def test_action_validator_work_and_exhaustion(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    # Work at campus store (valid)
    state = AgentStateSnapshot(agent_id="worker", location_id="campus_store", energy=50.0)
    default_campus.move_agent("worker", None, "campus_store")

    action = ProposedAction(agent_id="worker", action_type=ActionType.WORK)
    is_valid, status, _ = ActionValidator.validate(action, state, default_campus, default_clock, {})
    assert is_valid
    assert status == ActionStatus.SUCCESS

    # Exhausted worker (energy < 10)
    state_tired = AgentStateSnapshot(
        agent_id="tired_worker", location_id="campus_store", energy=5.0
    )
    is_valid, status, reason = ActionValidator.validate(
        action, state_tired, default_campus, default_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.FAILED_PREREQUISITE
    assert "exhausted" in reason.lower()


def test_action_validator_help_and_share_info(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    default_campus.move_agent("helper", None, "dining_hall")
    default_campus.move_agent("recipient", None, "dining_hall")

    state_helper = AgentStateSnapshot(agent_id="helper", location_id="dining_hall", money=50.0)

    # Valid help with money transfer
    help_action = ProposedAction(
        agent_id="helper",
        action_type=ActionType.HELP_AGENT,
        target_agent_id="recipient",
        amount=15.0,
    )
    is_valid, status, _ = ActionValidator.validate(
        help_action, state_helper, default_campus, default_clock, {}
    )
    assert is_valid
    assert status == ActionStatus.SUCCESS

    # Valid info share
    share_action = ProposedAction(
        agent_id="helper",
        action_type=ActionType.SHARE_INFO,
        target_agent_id="recipient",
        info_payload={"rumor": "Price hike next week"},
    )
    is_valid, status, _ = ActionValidator.validate(
        share_action, state_helper, default_campus, default_clock, {}
    )
    assert is_valid
    assert status == ActionStatus.SUCCESS


def test_action_validator_move_same_location_rejected(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    state = AgentStateSnapshot(agent_id="agent_1", location_id="dorm_north")
    action = ProposedAction(
        agent_id="agent_1",
        action_type=ActionType.MOVE,
        target_location_id="dorm_north",
    )
    is_valid, status, reason = ActionValidator.validate(
        action, state, default_campus, default_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.REJECTED
    assert "already at" in reason.lower()


def test_action_validator_rest_and_study_restrictions(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    # Library allows rest and study
    state_lib = AgentStateSnapshot(agent_id="scholar", location_id="central_library", energy=50.0)
    default_campus.move_agent("scholar", None, "central_library")

    rest_action = ProposedAction(agent_id="scholar", action_type=ActionType.REST)
    is_valid, status, _ = ActionValidator.validate(
        rest_action, state_lib, default_campus, default_clock, {}
    )
    assert is_valid
    assert status == ActionStatus.SUCCESS

    # Exhausted student trying to study (energy < 5)
    state_exhausted = AgentStateSnapshot(
        agent_id="exhausted", location_id="central_library", energy=2.0
    )
    study_action = ProposedAction(agent_id="exhausted", action_type=ActionType.STUDY)
    is_valid, status, reason = ActionValidator.validate(
        study_action, state_exhausted, default_campus, default_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.FAILED_PREREQUISITE
    assert "exhausted" in reason.lower()


def test_action_validator_purchase_item_checks(
    default_campus: CampusEnvironment, default_clock: SimulationClock
) -> None:
    state = AgentStateSnapshot(agent_id="shopper", location_id="campus_store", money=20.0)
    default_campus.move_agent("shopper", None, "campus_store")

    # Valid purchase
    buy_action = ProposedAction(
        agent_id="shopper", action_type=ActionType.PURCHASE_ITEM, amount=10.0
    )
    is_valid, status, _ = ActionValidator.validate(
        buy_action, state, default_campus, default_clock, {}
    )
    assert is_valid
    assert status == ActionStatus.SUCCESS

    # Overdraft purchase
    expensive_buy = ProposedAction(
        agent_id="shopper", action_type=ActionType.PURCHASE_ITEM, amount=50.0
    )
    is_valid, status, reason = ActionValidator.validate(
        expensive_buy, state, default_campus, default_clock, {}
    )
    assert not is_valid
    assert status == ActionStatus.FAILED_PREREQUISITE
    assert "insufficient funds" in reason.lower()
