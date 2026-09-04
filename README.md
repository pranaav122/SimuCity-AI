# SimuCity AI — Autonomous Multi-Agent Emergence Research Platform

**SimuCity AI** is a research-grade simulation platform designed to investigate a fundamental AI research question:

> **Can autonomous LLM-powered agents interacting in a shared, resource-constrained environment produce measurable emergent collective behavior?**

SimuCity AI provides a deterministic simulation substrate populated by heterogeneous, autonomous cognitive agents governed by homeostatic needs, 7-dimensional personality vectors, hierarchical goals, episodic memory streams, and dynamic social relationship networks.

---

## Key Architectural Principles

1. **Strict Separation of Reality and Reasoning**: The LLM never directly mutates world state. LLMs propose candidate actions, which pass through a deterministic physical validator before state execution.
2. **Deterministic Reproducibility**: All spatial movement, environmental clock progression, price dynamics, and stochastic distributions are tied to explicit seeds, ensuring bit-for-bit reproducible trajectories.
3. **Model Interchangeability**: Agnostic provider layer supporting **Claude 3.5 Sonnet**, **Google Gemini 2.5 Flash**, and high-speed **Deterministic Heuristic Mocks**.
4. **Autonomous Emergence Detection**: Real-time algorithmic detectors for organic community formation, scarcity-induced cooperation surges, information rumors cascades, and wealth inequality bifurcation.
5. **Interactive Research Dashboard**: React + Tailwind + Chart.js web interface featuring spatial campus topology, agent cognitive inspectors, longitudinal telemetries, and 3-way cross-model benchmark labs.

---

## System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        EXPERIMENT CONTROLLER                           │
│   (Declarative Config, Seeds, Model Benchmarks, Longitudinal Metrics)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
          ┌─────────────────────────┴─────────────────────────┐
          ▼                                                   ▼
┌──────────────────────────────┐            ┌──────────────────────────────────┐
│     COGNITIVE SIMUAGENTS     │            │    DETERMINISTIC SIMULATION      │
│  - 7D Personality Vectors    │            │  - Discrete Simulation Clock     │
│  - Homeostatic Needs Engine  │            │  - 9-Node Campus Spatial Graph   │
│  - Hierarchical Goals        │            │  - Action Validator & Mutator    │
│  - Episodic Memory Stream    │            │  - Dynamic Event & Shock Engine  │
│  - Dyadic Social Graph       │            │  - Information Cascade Ledger    │
│  - LLM Provider Abstraction  │            │  - Immutable State Snapshots     │
└──────────────┬───────────────┘            └─────────────────┬────────────────┘
               │                                              │
               │               PROPOSED ACTIONS               │
               ├─────────────────────────────────────────────►│
               │                                              │
               │            VALIDATED STATE DELTAS            │
               │◄─────────────────────────────────────────────┤
               │                                              │
               ▼                                              ▼
┌──────────────────────────────┐            ┌──────────────────────────────────┐
│     EMERGENCE DETECTORS      │            │       POSTGRES / SQLITE DB       │
│  - Spontaneous Clustering    │            │  - Experiments & Snapshots       │
│  - Altruistic Surges         │            │  - Longitudinal Metrics Series   │
│  - Rumor Cascades            │            │  - Emergent Pattern Discoveries  │
│  - Gini Wealth Bifurcation   │            │  - Complete Telemetry Logs       │
└──────────────────────────────┘            └──────────────────────────────────┘
```

---

## Quickstart & Installation

### 1. Prerequisites
- Python 3.10+
- Recommended: Virtual environment

### 2. Install Dependencies
```bash
pip install -e .
pip install fastapi uvicorn httpx pytest pytest-cov
```

### 3. Run the Automated Test Suite
```bash
pytest -v --cov=simucity
```

### 4. Launch the Research API & Web Dashboard
```bash
python -m uvicorn simucity.api.main:app --app-dir src --host 127.0.0.1 --port 8000 --reload
```

Visit **`http://127.0.0.1:8000/dashboard`** in your browser to interact with the visual simulation laboratory.

---

## Running Experiments via Python API

```python
from simucity.experiments import ExperimentConfig, ExperimentRunner

# 1. Define Experiment Configuration
config = ExperimentConfig(
    experiment_id="exp_campus_scarcity_01",
    name="Cafeteria Price Shock Study",
    number_of_agents=16,
    simulation_days=7,
    model="mock",  # 'claude', 'gemini', or 'mock'
    event_scenario="cafeteria_price_increase",
    seed=42,
)

# 2. Execute Simulation Run
runner = ExperimentRunner(config)
result = runner.run()

# 3. Inspect Quantitative Outcomes
print(f"Total Ticks Executed: {result.total_ticks}")
print(f"Final Gini Inequality: {result.final_metrics.gini_wealth}")
print(f"Final Cooperation Rate: {result.final_metrics.cooperation_rate * 100:.1f}%")
print(f"Emergent Patterns Detected: {len(result.detected_patterns)}")
```

---

## Documentation Index

- [Architecture & World Engine](docs/architecture.md)
- [Agent Cognitive Core & Decision Pipeline](docs/agent-design.md)
- [Experiment Methodology & Reproducibility](docs/experiment-design.md)
- [Quantitative Telemetry & Emergence Metrics](docs/metrics.md)
- [Research Findings & Notes](docs/research-notes.md)
