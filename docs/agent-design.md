# Agent Cognitive Core & Decision Pipeline

## 1. Internal Agent Representation

Every autonomous agent in SimuCity AI maintains a rich internal state:

```text
SimuAgent
├── id, name, age
├── 7D Personality Vector
│   ├── extroversion       [0.0 - 1.0]
│   ├── risk_tolerance     [0.0 - 1.0]
│   ├── cooperation        [0.0 - 1.0]
│   ├── ambition           [0.0 - 1.0]
│   ├── patience           [0.0 - 1.0]
│   ├── trust              [0.0 - 1.0]
│   └── curiosity          [0.0 - 1.0]
├── Homeostatic Needs
│   ├── hunger             [0 - 100]
│   ├── energy             [0 - 100]
│   ├── stress             [0 - 100]
│   ├── social             [0 - 100]
│   └── knowledge          [0 - 100]
├── Hierarchical Goal Priority Hierarchy
├── Memory Stream (Short-term FIFO + Long-term ranked episodic store)
├── Dyadic Social Relationship Network
└── Daily Routine & Strategic Plan
```

## 2. Episodic Memory Retrieval Scoring

When an agent reflects or plans, memory items are scored according to a composite multi-factor ranking function:

$$\text{Score}(m) = \alpha \cdot \text{Recency}(m) + \beta \cdot \text{Importance}(m) + \gamma \cdot \text{Relevance}(m, q)$$

Where:
- $\text{Recency}(m) = \delta^{\Delta t}$ (exponential decay with $\delta = 0.99$).
- $\text{Importance}(m) \in [0.1, 1.0]$ (significance rating).
- $\text{Relevance}(m, q) \in [0.0, 1.0]$ (lexical and semantic overlap with current decision context $q$).

## 3. Social Bonds & Reciprocal Ties

Relationships between pairs of agents are tracked along 5 continuous axes:
- **Trust** ($-100$ to $+100$)
- **Friendship** ($-100$ to $+100$)
- **Hostility** ($0$ to $+100$)
- **Respect** ($0$ to $+100$)
- **Familiarity** ($0$ to $+100$)

Positive collaborative actions (e.g. `HELP_AGENT`, `SOCIALIZE`) progressively build trust and affection, whereas broken commitments or conflicting actions induce hostility.
