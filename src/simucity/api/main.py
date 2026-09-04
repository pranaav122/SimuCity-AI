"""FastAPI server for SimuCity AI simulation research platform."""

import os
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from simucity.core.environment import CampusEnvironment
from simucity.database.db import SimulationDatabase
from simucity.experiments.experiment_runner import (
    ExperimentConfig,
    ExperimentRunner,
)

app = FastAPI(
    title="SimuCity AI — Autonomous Multi-Agent Simulation API",
    description=(
        "Research-grade multi-agent simulation API for studying decision-making, "
        "cooperation, and emergent collective behavior."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SimulationDatabase()

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend"
)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """Returns structured JSON for all unhandled exceptions."""
    status = 500
    if isinstance(exc, EnvironmentError):
        status = 422
    return JSONResponse(
        status_code=status,
        content={"detail": str(exc), "type": type(exc).__name__},
    )


@app.get("/")
@app.get("/dashboard")
def get_dashboard() -> FileResponse:
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Dashboard not found. Build the frontend first.")


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "SimuCity AI Engine", "version": "1.0.0"}


@app.get("/api/campus/topology")
def get_campus_topology() -> Dict[str, Any]:
    env = CampusEnvironment.create_default_campus()
    locs = [loc.model_dump() for loc in env.get_all_locations()]
    edges = []
    for u, v, data in env._graph.edges(data=True):
        edges.append({"source": u, "target": v, "travel_ticks": data.get("weight", 1)})
    return {"locations": locs, "paths": edges}


# ── Accepted model values ─────────────────────────────────────────────────────
ModelLiteral = Literal["mock", "claude", "gemini"]


class RunExperimentRequest(BaseModel):
    experiment_id: Optional[str] = None
    name: str = "Campus Emergence Study"
    number_of_agents: int = Field(default=16, ge=2, le=200)
    simulation_days: int = Field(default=3, ge=1, le=60)
    model: ModelLiteral = Field(default="mock", description="'claude' | 'gemini' | 'mock'")
    event_scenario: Optional[str] = None
    seed: int = 42


@app.post("/api/experiments/run", response_model=Dict[str, Any])
def run_experiment(req: RunExperimentRequest) -> Dict[str, Any]:
    exp_id = req.experiment_id or f"exp_{req.model}_{req.seed}_{int(req.number_of_agents)}a"
    config = ExperimentConfig(
        experiment_id=exp_id,
        name=req.name,
        number_of_agents=req.number_of_agents,
        simulation_days=req.simulation_days,
        model=req.model,
        event_scenario=req.event_scenario,
        seed=req.seed,
    )
    try:
        runner = ExperimentRunner(config)
    except EnvironmentError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = runner.run()
    db.save_experiment_result(result)
    return {
        "status": "completed",
        "experiment_id": exp_id,
        "model": req.model,
        "duration_seconds": result.duration_seconds,
        "total_ticks": result.total_ticks,
        "total_tokens": result.total_tokens,
        "total_cost_usd": result.total_cost_usd,
        "average_latency_ms": result.average_latency_ms,
        "patterns_detected": len(result.detected_patterns),
    }


@app.get("/api/experiments", response_model=List[Dict[str, Any]])
def list_experiments() -> List[Dict[str, Any]]:
    return db.list_experiments()


@app.get("/api/experiments/compare/models")
def compare_models(seed: int = 42, num_agents: int = 16, days: int = 3) -> Dict[str, Any]:
    """Benchmarks mock (always), claude (if ANTHROPIC_API_KEY set), gemini (if GEMINI_API_KEY set).

    Models with missing keys are returned as skipped with a clear reason.
    Results are genuinely different: mock uses heuristic, claude/gemini use real API calls.
    """
    results: Dict[str, Any] = {}

    for model_name in ["mock", "claude", "gemini"]:
        exp_id = f"benchmark_{model_name}_s{seed}_n{num_agents}"
        config = ExperimentConfig(
            experiment_id=exp_id,
            name=f"Model Comparison: {model_name.upper()}",
            number_of_agents=num_agents,
            simulation_days=days,
            model=model_name,  # type: ignore[arg-type]
            seed=seed,
        )
        try:
            runner = ExperimentRunner(config)
        except EnvironmentError as exc:
            results[model_name] = {
                "model": model_name,
                "skipped": True,
                "reason": str(exc),
            }
            continue

        res = runner.run()
        db.save_experiment_result(res)

        final_m = res.final_metrics
        results[model_name] = {
            "model": model_name,
            "skipped": False,
            "duration_seconds": res.duration_seconds,
            "total_tokens": res.total_tokens,
            "total_cost_usd": res.total_cost_usd,
            "average_latency_ms": res.average_latency_ms,
            "gini_wealth": final_m.gini_wealth if final_m else 0.0,
            "average_gpa": final_m.average_gpa if final_m else 0.0,
            "cooperation_rate": final_m.cooperation_rate if final_m else 0.0,
            "average_stress": final_m.average_stress if final_m else 0.0,
            "patterns_detected_count": len(res.detected_patterns),
        }

    return results


@app.get("/api/experiments/{experiment_id}")
def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    data = db.get_experiment(experiment_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return data
