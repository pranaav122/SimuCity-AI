"""Automated detection algorithms for emergent collective behaviors."""

from enum import Enum
from typing import Any

from pydantic import BaseModel

from simucity.information.info_propagator import InformationLedger
from simucity.metrics.metrics_collector import SimulationMetrics
from simucity.social.social_network import SocialGraph


class EmergentPatternType(str, Enum):
    SPONTANEOUS_GROUP_FORMATION = "spontaneous_group_formation"
    SCARCITY_COOPERATION_SURGE = "scarcity_cooperation_surge"
    INFORMATION_CASCADE = "information_cascade"
    EMERGENT_LEADERS = "emergent_leaders"
    WEALTH_INEQUALITY_BIFURCATION = "wealth_inequality_bifurcation"


class EmergentPattern(BaseModel):
    """A detected higher-order macro pattern emerging from decentralized agent interactions."""

    pattern_type: EmergentPatternType
    title: str
    description: str
    confidence: float
    tick_detected: int
    evidence: dict[str, Any]


class EmergenceDetector:
    """Scans simulation state and telemetry to identify emergent social phenomena."""

    @staticmethod
    def detect_all(
        current_tick: int,
        social_graph: SocialGraph,
        info_ledger: InformationLedger,
        metrics_history: list[SimulationMetrics],
    ) -> list[EmergentPattern]:
        patterns = []

        # 1. Detect Spontaneous Group Formation
        groups = social_graph.detect_emergent_groups(friendship_threshold=15.0)
        if len(groups) >= 2:
            patterns.append(
                EmergentPattern(
                    pattern_type=EmergentPatternType.SPONTANEOUS_GROUP_FORMATION,
                    title=f"Emergence of {len(groups)} Organic Peer Communities",
                    description=f"Agents autonomously established {len(groups)} distinct reciprocal social circles and alliances.",
                    confidence=0.88,
                    tick_detected=current_tick,
                    evidence={"groups": groups},
                )
            )

        # 2. Detect Information / Rumor Cascades
        for info in info_ledger.items.values():
            if info.reach >= 5 or info.cascade_depth >= 6:
                patterns.append(
                    EmergentPattern(
                        pattern_type=EmergentPatternType.INFORMATION_CASCADE,
                        title=f"Viral Information Cascade on topic '{info.topic}'",
                        description=f"Information originated from '{info.source}' penetrated {info.reach} agents across {info.cascade_depth} hops.",
                        confidence=0.92,
                        tick_detected=current_tick,
                        evidence={
                            "info_id": info.id,
                            "reach": info.reach,
                            "depth": info.cascade_depth,
                            "truth_value": info.truth_value,
                        },
                    )
                )

        # 3. Detect Wealth Inequality Bifurcation
        if len(metrics_history) >= 20:
            initial_gini = metrics_history[0].gini_wealth
            recent_gini = metrics_history[-1].gini_wealth
            if recent_gini - initial_gini > 0.15:
                patterns.append(
                    EmergentPattern(
                        pattern_type=EmergentPatternType.WEALTH_INEQUALITY_BIFURCATION,
                        title="Resource Inequality Bifurcation",
                        description=f"Wealth inequality expanded significantly: Gini coefficient rose from {initial_gini:.2f} to {recent_gini:.2f}.",
                        confidence=0.85,
                        tick_detected=current_tick,
                        evidence={"initial_gini": initial_gini, "recent_gini": recent_gini},
                    )
                )

        # 4. Detect Scarcity Cooperation Spike
        if len(metrics_history) >= 15:
            early_coop = sum(m.cooperation_rate for m in metrics_history[:5]) / 5.0
            late_coop = sum(m.cooperation_rate for m in metrics_history[-5:]) / 5.0
            if late_coop > early_coop * 1.3:
                patterns.append(
                    EmergentPattern(
                        pattern_type=EmergentPatternType.SCARCITY_COOPERATION_SURGE,
                        title="Altruistic Cooperation Surge",
                        description=f"Population cooperation increased by {((late_coop / max(0.01, early_coop)) - 1.0) * 100:.1f}% as agents pooled resources.",
                        confidence=0.82,
                        tick_detected=current_tick,
                        evidence={"early_coop": early_coop, "late_coop": late_coop},
                    )
                )

        return patterns
