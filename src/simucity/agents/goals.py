"""Hierarchical agent goals, utility evaluation, and objective tracking."""

from enum import Enum

from pydantic import BaseModel, Field


class GoalCategory(str, Enum):
    ACADEMIC = "academic"
    SOCIAL = "social"
    FINANCIAL = "financial"
    WELLNESS = "wellness"
    LEISURE = "leisure"


class AgentGoal(BaseModel):
    """An objective pursued by an agent with an explicit priority weight."""

    id: str
    title: str
    category: GoalCategory
    priority: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Priority weight (0.0=lowest, 1.0=highest)"
    )
    target_description: str = ""
    target_value: float = 0.0
    current_progress: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Completion fraction [0.0 - 1.0]"
    )
    is_completed: bool = False

    def update_progress(self, current_val: float) -> None:
        if self.target_value > 0:
            self.current_progress = min(1.0, max(0.0, current_val / self.target_value))
            if self.current_progress >= 1.0:
                self.is_completed = True


def create_default_goals(archetype: str = "balanced") -> list[AgentGoal]:
    """Generates standard goal configurations for agents."""
    if archetype == "scholar":
        return [
            AgentGoal(
                id="g_gpa",
                title="Maintain High GPA (>=3.8)",
                category=GoalCategory.ACADEMIC,
                priority=0.9,
                target_value=3.8,
            ),
            AgentGoal(
                id="g_stress",
                title="Keep Stress Low",
                category=GoalCategory.WELLNESS,
                priority=0.6,
                target_value=30.0,
            ),
            AgentGoal(
                id="g_friends",
                title="Build Study Network",
                category=GoalCategory.SOCIAL,
                priority=0.4,
                target_value=3.0,
            ),
        ]
    elif archetype == "socialite":
        return [
            AgentGoal(
                id="g_friends",
                title="Make Many Friends (>=6)",
                category=GoalCategory.SOCIAL,
                priority=0.95,
                target_value=6.0,
            ),
            AgentGoal(
                id="g_leisure",
                title="Enjoy Recreation & Parties",
                category=GoalCategory.LEISURE,
                priority=0.7,
                target_value=80.0,
            ),
            AgentGoal(
                id="g_gpa",
                title="Pass Classes (>=2.5)",
                category=GoalCategory.ACADEMIC,
                priority=0.4,
                target_value=2.5,
            ),
        ]
    elif archetype == "entrepreneur":
        return [
            AgentGoal(
                id="g_wealth",
                title="Accumulate Wealth (>= $300)",
                category=GoalCategory.FINANCIAL,
                priority=0.9,
                target_value=300.0,
            ),
            AgentGoal(
                id="g_network",
                title="Expand Professional Network",
                category=GoalCategory.SOCIAL,
                priority=0.7,
                target_value=5.0,
            ),
            AgentGoal(
                id="g_gpa",
                title="Maintain Decent GPA (>=3.0)",
                category=GoalCategory.ACADEMIC,
                priority=0.5,
                target_value=3.0,
            ),
        ]
    else:  # Balanced student
        return [
            AgentGoal(
                id="g_gpa",
                title="Maintain Good GPA (>=3.2)",
                category=GoalCategory.ACADEMIC,
                priority=0.7,
                target_value=3.2,
            ),
            AgentGoal(
                id="g_friends",
                title="Make Friends",
                category=GoalCategory.SOCIAL,
                priority=0.6,
                target_value=4.0,
            ),
            AgentGoal(
                id="g_budget",
                title="Stay Solvent (>= $100)",
                category=GoalCategory.FINANCIAL,
                priority=0.6,
                target_value=100.0,
            ),
            AgentGoal(
                id="g_wellness",
                title="Avoid Burnout",
                category=GoalCategory.WELLNESS,
                priority=0.5,
                target_value=40.0,
            ),
        ]
