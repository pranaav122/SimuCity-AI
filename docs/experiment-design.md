# Experiment Methodology & Reproducibility Matrix

## 1. Declarative Experiment Configuration

Experiments are specified declaratively as reproducible JSON objects:

```json
{
  "experiment_id": "exp_scarcity_claude_vs_gemini_s42",
  "name": "Scarcity & Altruism Study",
  "number_of_agents": 24,
  "simulation_days": 14,
  "model": "claude",
  "event_scenario": "cafeteria_price_increase",
  "seed": 42
}
```

## 2. Experimental Controls & Isolation

To isolate whether emergent patterns stem from model reasoning versus random noise:
1. **Seed Anchoring**: Initial agent wealth, personalities, and stochastic event times are identical across model comparison runs.
2. **Deterministic Substrate**: The environment, physical transit, opening hours, and metabolism formulas remain 100% deterministic.
3. **Identical Prompt Templates**: Claude, Gemini, and local models receive strictly identical context structures and JSON schemas.

## 3. Exogenous Shock Scenarios
- **Cafeteria Price Surge (+25%)**: Tests how agents reallocate budgets, whether high-income agents provide mutual aid, and whether dietary stress increases.
- **Surprise Midterm Exam**: Introduces acute academic stress and spreads rumors through the student body, measuring information cascade speeds and study group formation.
- **Campus Transit Strike**: Disrupts central travel lanes, measuring spatial congestion shifts and agent adaptability.
