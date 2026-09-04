"""Unit tests for FastAPI REST endpoints."""

from fastapi.testclient import TestClient
from simucity.api.main import app

client = TestClient(app)


def test_health_and_topology_endpoints() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    topo_resp = client.get("/api/campus/topology")
    assert topo_resp.status_code == 200
    data = topo_resp.json()
    assert len(data["locations"]) == 9
    assert len(data["paths"]) > 0


def test_run_and_retrieve_experiment_via_api() -> None:
    # Run short experiment
    run_payload = {
        "experiment_id": "api_test_exp_01",
        "name": "API Test Run",
        "number_of_agents": 6,
        "simulation_days": 1,
        "model": "mock",
        "seed": 42,
    }
    resp = client.post("/api/experiments/run", json=run_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    # List experiments
    list_resp = client.get("/api/experiments")
    assert list_resp.status_code == 200
    assert any(e["experiment_id"] == "api_test_exp_01" for e in list_resp.json())

    # Get details
    detail_resp = client.get("/api/experiments/api_test_exp_01")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert len(detail_data["metrics"]) >= 96
    assert len(detail_data["agents"]) == 6
