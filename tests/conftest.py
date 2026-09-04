"""Shared pytest fixtures for SimuCity test suite."""

import pytest
from simucity.core.clock import SimulationClock
from simucity.core.engine import SimulationEngine
from simucity.core.environment import CampusEnvironment


@pytest.fixture
def default_clock() -> SimulationClock:
    """Fixture providing a clock starting at Day 1, 08:00 AM (Monday)."""
    return SimulationClock(current_tick=0, minutes_per_tick=15, start_day=1, start_hour=8, start_minute=0)


@pytest.fixture
def default_campus() -> CampusEnvironment:
    """Fixture providing standard university campus environment."""
    return CampusEnvironment.create_default_campus()


@pytest.fixture
def default_engine(default_campus: CampusEnvironment, default_clock: SimulationClock) -> SimulationEngine:
    """Fixture providing an initialized simulation engine with seed 42."""
    return SimulationEngine(seed=42, environment=default_campus, clock=default_clock)
