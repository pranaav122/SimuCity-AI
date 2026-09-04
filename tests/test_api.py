"""Tests for FastAPI REST endpoints."""

import pytest
from fastapi.testclient import TestClient

from simucity.api.main import app

client = TestClient(app)


def test_health_and_topology_endpoints(tmp_db: str) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data

    topo_resp = client.get("/api/campus/topology")
    assert topo_resp.status_code == 200
    data = topo_resp.json()
    assert len(data["locations"]) == 9
    assert len(data["paths"]) > 0


def test_dashboard_serves_html(tmp_db: str) -> None:
    """GET /dashboard must return 200 with Content-Type: text/html."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


def test_run_experiment_mock_and_retrieve(tmp_db: str) -> None:
    """Run a short mock experiment and retrieve its full details."""
    run_payload = {
        "experiment_id": "api_test_mock_01",
        "name": "API Test Run",
        "number_of_agents": 4,
        "simulation_days": 1,
        "model": "mock",
        "seed": 42,
    }
    resp = client.post("/api/experiments/run", json=run_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["total_ticks"] == 96
    assert body["model"] == "mock"

    # List experiments
    list_resp = client.get("/api/experiments")
    assert list_resp.status_code == 200
    assert any(e["experiment_id"] == "api_test_mock_01" for e in list_resp.json())

    # Get details — verify exact row counts (idempotent after fix)
    detail_resp = client.get("/api/experiments/api_test_mock_01")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert len(detail_data["metrics"]) == 96
    assert len(detail_data["agents"]) == 4
    assert "patterns" in detail_data


def test_run_experiment_idempotent(tmp_db: str) -> None:
    """Re-running the same experiment_id must not duplicate metrics rows."""
    payload = {
        "experiment_id": "api_idem_test",
        "number_of_agents": 3,
        "simulation_days": 1,
        "model": "mock",
        "seed": 7,
    }
    client.post("/api/experiments/run", json=payload)
    client.post("/api/experiments/run", json=payload)

    detail_resp = client.get("/api/experiments/api_idem_test")
    assert detail_resp.status_code == 200
    # Must have exactly 96 metrics rows — not 192
    assert len(detail_resp.json()["metrics"]) == 96


def test_experiment_not_found(tmp_db: str) -> None:
    resp = client.get("/api/experiments/nonexistent_experiment_xyz")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_run_experiment_invalid_model(tmp_db: str) -> None:
    """Providing an invalid model name must return 422 Unprocessable Entity."""
    resp = client.post(
        "/api/experiments/run",
        json={
            "experiment_id": "bad_model",
            "model": "gpt-99",
            "number_of_agents": 2,
            "simulation_days": 1,
        },
    )
    assert resp.status_code == 422


def test_run_experiment_claude_no_key(tmp_db: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Requesting model='claude' without ANTHROPIC_API_KEY must return 422."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    resp = client.post(
        "/api/experiments/run",
        json={
            "experiment_id": "claude_no_key",
            "model": "claude",
            "number_of_agents": 2,
            "simulation_days": 1,
        },
    )
    assert resp.status_code == 422
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]


def test_run_experiment_gemini_no_key(tmp_db: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Requesting model='gemini' without GEMINI_API_KEY must return 422."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    resp = client.post(
        "/api/experiments/run",
        json={
            "experiment_id": "gemini_no_key",
            "model": "gemini",
            "number_of_agents": 2,
            "simulation_days": 1,
        },
    )
    assert resp.status_code == 422
    assert "GEMINI_API_KEY" in resp.json()["detail"]


def test_compare_models_returns_mock_and_skips_llms(
    tmp_db: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no API keys, compare endpoint must return mock result and mark others as skipped."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    resp = client.get("/api/experiments/compare/models?seed=42&num_agents=3&days=1")
    assert resp.status_code == 200
    data = resp.json()

    assert "mock" in data
    assert data["mock"]["skipped"] is False
    assert data["mock"]["cooperation_rate"] >= 0.0

    # Claude and Gemini must be marked skipped, not silently run
    assert data["claude"]["skipped"] is True
    assert "ANTHROPIC_API_KEY" in data["claude"]["reason"]
    assert data["gemini"]["skipped"] is True
    assert "GEMINI_API_KEY" in data["gemini"]["reason"]
