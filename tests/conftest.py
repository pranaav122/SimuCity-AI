"""Shared pytest fixtures for SimuCity test suite."""

import os
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


@pytest.fixture
def tmp_db(tmp_path: "pytest.TempPathFactory", monkeypatch: pytest.MonkeyPatch) -> str:
    """Fixture that redirects SimulationDatabase to a temp file for each test.

    Prevents cross-test DB state accumulation and avoids touching the project
    simucity.db file during the test run.
    """
    db_path = str(tmp_path / "test_simucity.db")
    # Patch the default db_path argument at the class level
    import simucity.database.db as db_module  # noqa: PLC0415

    original_init = db_module.SimulationDatabase.__init__

    def patched_init(self: db_module.SimulationDatabase, db_path_arg: str = db_path) -> None:
        original_init(self, db_path_arg)

    monkeypatch.setattr(db_module.SimulationDatabase, "__init__", patched_init)

    # Also patch the global `db` singleton in api.main so API tests get the tmp DB
    try:
        import simucity.api.main as api_module  # noqa: PLC0415
        original_db = api_module.db
        api_module.db = db_module.SimulationDatabase(db_path)
        yield db_path
        api_module.db = original_db
    except Exception:
        yield db_path
