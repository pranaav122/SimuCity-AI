"""Unit tests for CampusEnvironment and Location graph."""

import pytest

from simucity.core.environment import (
    CampusEnvironment,
    Location,
    LocationAffordance,
    LocationType,
)


def test_default_campus_initialization(default_campus: CampusEnvironment) -> None:
    locations = default_campus.get_all_locations()
    assert len(locations) == 9

    dorm_north = default_campus.get_location("dorm_north")
    assert dorm_north.type == LocationType.DORMITORY
    assert dorm_north.capacity == 120
    assert dorm_north.allows(LocationAffordance.SLEEP)
    assert dorm_north.allows(LocationAffordance.REST)
    assert not dorm_north.allows(LocationAffordance.ATTEND_CLASS)


def test_environment_shortest_paths(default_campus: CampusEnvironment) -> None:
    # Direct edge
    ticks = default_campus.get_travel_ticks("dorm_north", "dining_hall")
    assert ticks == 1

    # Multi-hop path: dorm_south -> rec_center -> transit_hub -> central_library
    ticks_multi = default_campus.get_travel_ticks("dorm_south", "central_library")
    assert ticks_multi >= 1

    # Same location
    assert default_campus.get_travel_ticks("dining_hall", "dining_hall") == 0


def test_location_opening_hours(default_campus: CampusEnvironment) -> None:
    classroom = default_campus.get_location("classroom_hall")
    # Classroom is open 08:00 - 18:00
    assert classroom.is_open(8)
    assert classroom.is_open(12)
    assert classroom.is_open(17)
    assert not classroom.is_open(18)
    assert not classroom.is_open(22)
    assert not classroom.is_open(6)

    # Dormitory is open 24/7
    dorm = default_campus.get_location("dorm_north")
    assert dorm.is_open(0)
    assert dorm.is_open(3)
    assert dorm.is_open(14)


def test_occupancy_and_capacity_limits() -> None:
    env = CampusEnvironment()
    loc = Location(
        id="small_room",
        name="Small Room",
        type=LocationType.CLASSROOM,
        capacity=2,
    )
    env.add_location(loc)

    assert env.move_agent("agent_1", None, "small_room")
    assert env.move_agent("agent_2", None, "small_room")
    assert loc.current_occupancy == 2
    assert not loc.has_capacity

    # Third agent should be rejected due to capacity limit
    assert not env.move_agent("agent_3", None, "small_room")
    assert loc.current_occupancy == 2

    # Removing an agent frees space
    loc.remove_occupant("agent_1")
    assert loc.has_capacity
    assert env.move_agent("agent_3", None, "small_room")
    assert loc.current_occupancy == 2


def test_co_located_agents(default_campus: CampusEnvironment) -> None:
    default_campus.move_agent("alice", None, "dining_hall")
    default_campus.move_agent("bob", None, "dining_hall")
    default_campus.move_agent("charlie", None, "central_library")

    alice_peers = default_campus.get_co_located_agents("alice")
    assert "bob" in alice_peers
    assert "charlie" not in alice_peers

    charlie_peers = default_campus.get_co_located_agents("charlie")
    assert charlie_peers == []


def test_environment_edge_cases(default_campus: CampusEnvironment) -> None:
    # Invalid location lookup
    with pytest.raises(KeyError):
        default_campus.get_location("non_existent_loc")

    # Invalid path lookup
    with pytest.raises(KeyError):
        default_campus.get_travel_ticks("dorm_north", "invalid_dest")

    # Crowding factor & available slots
    loc = default_campus.get_location("dorm_north")
    assert loc.available_slots == 120
    assert loc.crowding_factor == 0.0

    default_campus.move_agent("agent_x", None, "dorm_north")
    assert loc.available_slots == 119
    assert default_campus.get_agent_location_id("agent_x") == "dorm_north"

    # Remove agent from all
    default_campus.remove_agent_from_all("agent_x")
    assert default_campus.get_agent_location_id("agent_x") is None
