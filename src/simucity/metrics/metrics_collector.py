"""Quantitative metrics calculation, Gini inequality, and population telemetry."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from simucity.core.actions import ActionResult, ActionType
from simucity.core.world_state import WorldStateSnapshot
from simucity.social.social_network import SocialGraph


class SimulationMetrics(BaseModel):
    """Aggregate quantitative metrics snapshot for a simulation tick."""

    tick: int
    day: int
    time_str: str
    population_size: int
    gini_wealth: float = Field(description="Gini coefficient of wealth distribution [0.0 = perfect equality, 1.0 = total inequality]")
    average_money: float
    average_gpa: float
    average_knowledge: float
    average_stress: float
    average_energy: float
    average_hunger: float
    average_social: float
    cooperation_rate: float = Field(description="Fraction of positive social/help actions [0.0 - 1.0]")
    conflict_count: int = 0
    active_groups_count: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0


class MetricsCollector:
    """Computes and tracks longitudinal telemetry across simulation runs."""

    def __init__(self) -> None:
        self.history: List[SimulationMetrics] = []

    @staticmethod
    def compute_gini(values: List[float]) -> float:
        """Calculates exact Gini coefficient for a distribution of positive values."""
        if not values or len(values) <= 1:
            return 0.0
        sorted_vals = sorted(values)
        n = len(values)
        total = sum(sorted_vals)
        if total == 0:
            return 0.0
        cumulative = 0.0
        for i, val in enumerate(sorted_vals, 1):
            cumulative += i * val
        gini = ((2.0 * cumulative) / (n * total)) - ((n + 1.0) / n)
        return max(0.0, min(1.0, round(gini, 4)))

    def compute_step_metrics(
        self,
        snapshot: WorldStateSnapshot,
        recent_actions: List[ActionResult],
        social_graph: SocialGraph,
        total_tokens: int = 0,
        total_cost: float = 0.0,
    ) -> SimulationMetrics:
        agents = list(snapshot.agent_states.values())
        pop_size = max(1, len(agents))

        money_vals = [a.money for a in agents]
        gini = self.compute_gini(money_vals)

        avg_money = sum(money_vals) / pop_size
        avg_gpa = sum(a.gpa for a in agents) / pop_size
        avg_knowledge = sum(a.knowledge for a in agents) / pop_size
        avg_stress = sum(a.stress for a in agents) / pop_size
        avg_energy = sum(a.energy for a in agents) / pop_size
        avg_hunger = sum(a.hunger for a in agents) / pop_size
        avg_social = sum(a.social for a in agents) / pop_size

        # Compute cooperation rate from recent actions
        pos_social = sum(1 for a in recent_actions if a.action.action_type in (ActionType.HELP_AGENT, ActionType.SOCIALIZE, ActionType.SHARE_INFO))
        total_social_ops = max(1, len(recent_actions))
        coop_rate = pos_social / float(total_social_ops)

        groups = social_graph.detect_emergent_groups()

        metrics = SimulationMetrics(
            tick=snapshot.tick,
            day=snapshot.day,
            time_str=snapshot.time_str,
            population_size=pop_size,
            gini_wealth=gini,
            average_money=round(avg_money, 2),
            average_gpa=round(avg_gpa, 2),
            average_knowledge=round(avg_knowledge, 2),
            average_stress=round(avg_stress, 2),
            average_energy=round(avg_energy, 2),
            average_hunger=round(avg_hunger, 2),
            average_social=round(avg_social, 2),
            cooperation_rate=round(coop_rate, 3),
            active_groups_count=len(groups),
            total_tokens_used=total_tokens,
            total_cost_usd=round(total_cost, 4),
        )
        self.history.append(metrics)
        return metrics

    def to_timeseries_dict(self) -> Dict[str, List[Any]]:
        return {
            "ticks": [m.tick for m in self.history],
            "gini_wealth": [m.gini_wealth for m in self.history],
            "average_money": [m.average_money for m in self.history],
            "average_gpa": [m.average_gpa for m in self.history],
            "average_stress": [m.average_stress for m in self.history],
            "average_knowledge": [m.average_knowledge for m in self.history],
            "cooperation_rate": [m.cooperation_rate for m in self.history],
            "active_groups": [m.active_groups_count for m in self.history],
        }
