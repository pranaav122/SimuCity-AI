# Architecture & World Engine Specification

## 1. Separation of Concerns

SimuCity AI is fundamentally built around the principle that **LLMs reason, but physics and rules execute**.

```text
┌──────────────┐
│  SimuAgent   │ (Reasoning, Social Intent, Memory Recall)
└──────┬───────┘
       │ ProposedAction (e.g. ActionType.EAT in "dining_hall")
       ▼
┌──────────────────┐
│ ActionValidator  │ (Checks opening hours, capacity, balance, energy, co-location)
└──────┬───────────┘
       │ Valid / Invalid Result
       ▼
┌──────────────────┐
│ SimulationEngine │ (Applies deterministic resource & vital deltas, updates world graph)
└──────┬───────────┘
       │ Immutable WorldStateSnapshot
       ▼
┌──────────────────┐
│ Database/Metrics │ (Persists time-series telemetry & emergence records)
└──────────────────┘
```

## 2. Discrete Simulation Clock
- 15 minutes per tick (96 ticks per calendar day).
- Tracks full week cycle (`Monday` through `Sunday`), hour of day, and environmental temporal predicates (`is_class_hours`, `is_night`, `is_meal_hours`).

## 3. Campus Topology Graph
- 9 distinct physical nodes: `dorm_north`, `dorm_south`, `classroom_hall`, `central_library`, `dining_hall`, `campus_store`, `rec_center`, `transit_hub`, `admin_center`.
- Weighted network edges calculate shortest path transit duration.
- Per-node properties: maximum simultaneous capacity, ambient crowd noise factor, hourly opening schedules, base amenity costs, and affordance sets.

## 4. Metabolism & Natural Decay
At every discrete tick, passive homeostatic equations update agent vitals:
- Hunger accumulation: $+0.6$ per 15-minute tick.
- Energy dissipation: $-0.5$ per tick when active.
- Social isolation decay: $-0.2$ per tick.
- Exhaustion & starvation compound stress escalation: $+1.0$ per tick when hunger $> 75$ or energy $< 15$.
