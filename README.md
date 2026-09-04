# SimuCity AI — Autonomous Multi-Agent Emergence Research Platform

[![CI](https://github.com/YOUR_ORG/simucity/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_ORG/simucity/actions/workflows/ci.yml)

**SimuCity AI** is a research-grade simulation platform designed to investigate a fundamental AI research question:

> **Can autonomous LLM-powered agents interacting in a shared, resource-constrained environment produce measurable emergent collective behavior?**

SimuCity AI provides a deterministic simulation substrate populated by heterogeneous, autonomous cognitive agents governed by homeostatic needs, 7-dimensional personality vectors, hierarchical goals, episodic memory streams, and dynamic social relationship networks.

---

## Key Architectural Principles

1. **Strict Separation of Reality and Reasoning**: The LLM never directly mutates world state. LLMs propose candidate actions, which pass through a deterministic physical validator before state execution.
2. **Deterministic Reproducibility**: All spatial movement, environmental clock progression, price dynamics, and stochastic distributions are tied to explicit seeds, ensuring bit-for-bit reproducible trajectories.
3. **Model Interchangeability**: Agnostic provider layer supporting **Claude 3.5 Sonnet**, **Google Gemini 2.0 Flash**, and a high-speed **Deterministic Heuristic Mock**.
4. **Autonomous Emergence Detection**: Real-time algorithmic detectors for organic community formation, scarcity-induced cooperation surges, information rumor cascades, and wealth inequality bifurcation.
5. **Interactive Research Dashboard**: Vanilla JS web interface featuring spatial campus topology, agent cognitive inspectors, longitudinal telemetries, and 3-way cross-model benchmark labs.

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
               │             PROPOSED ACTIONS                 │
               ├─────────────────────────────────────────────►│
               │                                              │
               │           VALIDATED STATE DELTAS             │
               │◄─────────────────────────────────────────────┤
               │                                              │
               ▼                                              ▼
┌──────────────────────────────┐            ┌──────────────────────────────────┐
│     EMERGENCE DETECTORS      │            │          SQLITE DATABASE         │
│  - Spontaneous Clustering    │            │  - Experiments & Snapshots       │
│  - Altruistic Surges         │            │  - Longitudinal Metrics Series   │
│  - Rumor Cascades            │            │  - Emergent Pattern Discoveries  │
│  - Gini Wealth Bifurcation   │            │  - Complete Telemetry Logs       │
└──────────────────────────────┘            └──────────────────────────────────┘
```

---

## Quickstart & Installation

### Prerequisites
- Python 3.10+
- Recommended: Virtual environment (`python -m venv .venv`)

### 1. Install (one command)

```bash
pip install -e ".[dev]"
```

This installs `simucity` plus all runtime dependencies (`fastapi`, `uvicorn`, `httpx`, `networkx`, `pydantic`) and dev tools (`pytest`, `ruff`, `mypy`).

> **For Gemini support**: additionally run `pip install -e ".[gemini]"` (installs `google-genai`).

### 2. Configure API Keys (optional — mock mode works without any keys)

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY and/or GEMINI_API_KEY
```

Without keys, only `model="mock"` works. The server starts and the dashboard is fully functional in mock mode.

### 3. Run Tests

```bash
pytest -v --cov=simucity
```

Expected: ≥55 tests, 0 failures.

### 4. Launch the API & Dashboard

```bash
python -m uvicorn simucity.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **`http://127.0.0.1:8000/dashboard`** in your browser.

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

## REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service health check |
| `GET` | `/api/campus/topology` | Campus graph structure |
| `POST` | `/api/experiments/run` | Run a simulation experiment |
| `GET` | `/api/experiments` | List all stored experiments |
| `GET` | `/api/experiments/{id}` | Get experiment details (metrics, agents, patterns) |
| `GET` | `/api/experiments/compare/models` | Run 3-way model benchmark |

### POST `/api/experiments/run` body

```json
{
  "experiment_id": "my_experiment",
  "number_of_agents": 16,
  "simulation_days": 3,
  "model": "mock",
  "event_scenario": "cafeteria_price_increase",
  "seed": 42
}
```

`model` must be `"mock"`, `"claude"`, or `"gemini"`. Claude/Gemini require their respective API keys.

---

## Environment Variables

| Variable | Required for | Description |
|----------|-------------|-------------|
| `ANTHROPIC_API_KEY` | `model="claude"` | Anthropic API key from [console.anthropic.com](https://console.anthropic.com/) |
| `GEMINI_API_KEY` | `model="gemini"` | Google AI Studio key from [aistudio.google.com](https://aistudio.google.com/app/apikey) |

Without keys set, requesting `claude` or `gemini` returns HTTP 422 with a clear message.

---

## Docker

```bash
# Build
docker build -t simucity-ai .

# Run (mock mode, no API keys needed)
docker run -p 8000:8000 simucity-ai

# Run with API keys
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e GEMINI_API_KEY=AIza... \
  simucity-ai

# Docker Compose
docker compose up
```

---

## Development

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/simucity --ignore-missing-imports

# Full test suite with coverage
pytest -v --cov=simucity --cov-report=term-missing
```

---

## Documentation Index

- [Architecture & World Engine](docs/architecture.md)
- [Agent Cognitive Core & Decision Pipeline](docs/agent-design.md)
- [Experiment Methodology & Reproducibility](docs/experiment-design.md)
- [Quantitative Telemetry & Emergence Metrics](docs/metrics.md)
- [Research Findings & Notes](docs/research-notes.md)

---

## Known Limitations

- **LLM latency**: Each tick calls the LLM once per agent — 16 agents × 96 ticks × 3 days = 4,608 API calls per run. This is intentional for research fidelity but costs real money and time.
- **SQLite**: Not suitable for concurrent multi-user load. For production multi-tenant use, replace with PostgreSQL.
- **No streaming**: Simulation runs synchronously on the API server — long runs (>10 agents, >7 days) will block the request. For production, use a background task queue (Celery/RQ).
