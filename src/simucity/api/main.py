"""FastAPI server for SimuCity AI simulation research platform."""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from simucity.core.environment import CampusEnvironment
from simucity.database.db import SimulationDatabase
from simucity.experiments.experiment_runner import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
)

import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="SimuCity AI — Autonomous Multi-Agent Simulation API",
    description="Research-grade multi-agent simulation API for studying decision-making, cooperation, and emergent collective behavior.",
    version="1.0.0",
)

# Enable CORS for Next.js / React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SimulationDatabase()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
@app.get("/dashboard")
def get_dashboard():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "SimuCity API Running. Dashboard index.html not found."}


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


class RunExperimentRequest(BaseModel):
    experiment_id: Optional[str] = None
    name: str = "Campus Emergence Study"
    number_of_agents: int = Field(default=16, ge=2, le=200)
    simulation_days: int = Field(default=3, ge=1, le=60)
    model: str = Field(default="mock", description="'claude' | 'gemini' | 'mock'")
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
    runner = ExperimentRunner(config)
    result = runner.run()
    db.save_experiment_result(result)
    return {
        "status": "completed",
        "experiment_id": exp_id,
        "duration_seconds": result.duration_seconds,
        "total_ticks": result.total_ticks,
        "total_tokens": result.total_tokens,
        "total_cost_usd": result.total_cost_usd,
        "patterns_detected": len(result.detected_patterns),
    }


@app.get("/api/experiments", response_model=List[Dict[str, Any]])
def list_experiments() -> List[Dict[str, Any]]:
    return db.list_experiments()


@app.get("/api/experiments/{experiment_id}")
def get_experiment_details(experiment_id: str) -> Dict[str, Any]:
    data = db.get_experiment(experiment_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")
    return data


@app.get("/api/experiments/compare/models")
def compare_models(seed: int = 42, num_agents: int = 16, days: int = 3) -> Dict[str, Any]:
    """Runs a direct benchmark comparison between models under identical seeds and conditions."""
    results = {}
    for model_name in ["mock", "gemini", "claude"]:
        exp_id = f"benchmark_{model_name}_s{seed}"
        config = ExperimentConfig(
            experiment_id=exp_id,
            name=f"Model Comparison: {model_name.upper()}",
            number_of_agents=num_agents,
            simulation_days=days,
            model=model_name,
            seed=seed,
        )
        runner = ExperimentRunner(config)
        res = runner.run()
        db.save_experiment_result(res)

        final_m = res.final_metrics
        results[model_name] = {
            "model": model_name,
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
