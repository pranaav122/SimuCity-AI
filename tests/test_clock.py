"""Unit tests for the SimulationClock."""

import pytest

from simucity.core.clock import SimulationClock


def test_clock_initial_state(default_clock: SimulationClock) -> None:
    assert default_clock.current_tick == 0
    assert default_clock.day == 1
    assert default_clock.hour == 8
    assert default_clock.minute == 0
    assert default_clock.time_str == "08:00"
    assert default_clock.day_of_week == "Monday"
    assert not default_clock.is_weekend
    assert not default_clock.is_night
    assert default_clock.is_class_hours
    assert default_clock.is_meal_hours


def test_clock_tick_advancement(default_clock: SimulationClock) -> None:
    # Advance 4 ticks (1 hour)
    default_clock.advance(4)
    assert default_clock.current_tick == 4
    assert default_clock.hour == 9
    assert default_clock.minute == 0
    assert default_clock.time_str == "09:00"

    # Advance 1 tick (15 minutes)
    default_clock.advance(1)
    assert default_clock.time_str == "09:15"


def test_clock_day_rollover() -> None:
    # 96 ticks per day with 15 min per tick
    clock = SimulationClock(start_day=1, start_hour=0, start_minute=0)
    assert clock.day == 1
    assert clock.day_of_week == "Monday"

    clock.advance(96)
    assert clock.day == 2
    assert clock.day_of_week == "Tuesday"
    assert clock.hour == 0
    assert clock.minute == 0

    # Advance to Saturday (Day 6)
    clock.advance(96 * 4)
    assert clock.day == 6
    assert clock.day_of_week == "Saturday"
    assert clock.is_weekend
    assert not clock.is_class_hours


def test_clock_night_and_meal_predicates() -> None:
    clock = SimulationClock(start_hour=23, start_minute=0)
    assert clock.is_night
    assert not clock.is_meal_hours

    clock_lunch = SimulationClock(start_hour=12, start_minute=30)
    assert clock_lunch.is_meal_hours
    assert not clock_lunch.is_night


def test_clock_invalid_advance() -> None:
    clock = SimulationClock()
    with pytest.raises(ValueError):
        clock.advance(-1)


def test_clock_properties_and_reset(default_clock: SimulationClock) -> None:
    assert default_clock.ticks_per_hour == 4
    assert default_clock.ticks_per_day == 96
    assert "Day 1 (Monday) 08:00 [Tick 0]" in default_clock.formatted

    default_clock.advance(10)
    assert default_clock.current_tick == 10
    default_clock.reset()
    assert default_clock.current_tick == 0
