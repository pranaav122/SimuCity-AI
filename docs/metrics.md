# Quantitative Telemetry & Emergence Metrics

## 1. Mathematical Metric Formulations

### Gini Wealth Coefficient
The platform measures resource inequality at each tick using the Gini coefficient:

$$G = \frac{\sum_{i=1}^n \sum_{j=1}^n |x_i - x_j|}{2n \sum_{i=1}^n x_i}$$

- $G = 0.0$: Perfect monetary equality.
- $G \to 1.0$: Total wealth concentration in a single agent.

### Cooperation Rate
The fraction of positive prosocial actions executed within a time window:

$$\text{Cooperation Rate} = \frac{N_{\text{help}} + N_{\text{socialize}} + N_{\text{share\_info}}}{N_{\text{total\_actions}}}$$

### Social Network Density
The connectivity ratio of reciprocal friendships across the campus graph:

$$\text{Density} = \frac{|E|}{|V|(|V|-1)}$$

---

## 2. Emergent Behavior Detection Criteria

1. **Spontaneous Group Formation**: Detected when the social network forms connected subgraphs with mutual friendship ratings $> 15.0$ and subgraph density $> 0.5$.
2. **Scarcity Cooperation Spike**: Detected when the post-shock cooperation rate exceeds the pre-shock baseline by $\ge 30\%$.
3. **Information Cascade**: Detected when a rumor reaches $\ge 5$ agents across $\ge 6$ transmission hops.
4. **Inequality Bifurcation**: Detected when the population Gini coefficient increases by $> 0.15$ over the course of the simulation.
