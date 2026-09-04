"""Unit tests for ExperimentRunner, Emergence Detection, and Database storage."""

from simucity.database.db import SimulationDatabase
from simucity.experiments.experiment_runner import (
    ExperimentConfig,
    ExperimentRunner,
)
from simucity.metrics.metrics_collector import MetricsCollector


def test_gini_calculation() -> None:
    # Perfect equality
    assert MetricsCollector.compute_gini([100.0, 100.0, 100.0, 100.0]) == 0.0

    # Extreme inequality
    gini_high = MetricsCollector.compute_gini([0.0, 0.0, 0.0, 1000.0])
    assert gini_high > 0.7


def test_full_experiment_run_and_db_persistence(tmp_path) -> None:
    db_file = str(tmp_path / "test_simucity.db")
    db = SimulationDatabase(db_path=db_file)

    config = ExperimentConfig(
        experiment_id="test_exp_01",
        name="Unit Test Experiment",
        number_of_agents=8,
        simulation_days=1,  # 96 ticks
        model="mock",
        event_scenario="cafeteria_price_increase",
        seed=42,
    )

    runner = ExperimentRunner(config)
    result = runner.run()

    assert result.total_ticks == 96
    assert len(result.all_metrics) == 96
    assert result.final_metrics is not None
    assert len(result.agent_summaries) == 8

    # Save to database
    db.save_experiment_result(result)

    # Retrieve and assert
    exp_record = db.get_experiment("test_exp_01")
    assert exp_record is not None
    assert exp_record["name"] == "Unit Test Experiment"
    assert len(exp_record["metrics"]) == 96
    assert len(exp_record["agents"]) == 8

    exp_list = db.list_experiments()
    assert len(exp_list) == 1
    assert exp_list[0]["experiment_id"] == "test_exp_01"
