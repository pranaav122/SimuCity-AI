"""Homeostatic needs and psychological drive mechanisms for agents."""

from pydantic import BaseModel, Field


class AgentNeeds(BaseModel):
    """Homeostatic needs vector for autonomous agents."""

    hunger: float = Field(default=20.0, ge=0.0, le=100.0, description="0=Satiated, 100=Starving")
    energy: float = Field(
        default=85.0, ge=0.0, le=100.0, description="100=Fully rested, 0=Exhausted"
    )
    stress: float = Field(default=15.0, ge=0.0, le=100.0, description="0=Zen, 100=Burnout")
    social: float = Field(
        default=60.0, ge=0.0, le=100.0, description="100=Socially fulfilled, 0=Isolated"
    )
    knowledge: float = Field(
        default=20.0, ge=0.0, le=100.0, description="Cumulative academic understanding"
    )

    def get_urgency_scores(self) -> dict[str, float]:
        """Calculates urgency weights [0.0 - 1.0] for addressing each fundamental drive."""
        return {
            "eat": self.hunger / 100.0,
            "sleep": (100.0 - self.energy) / 100.0,
            "destress": self.stress / 100.0,
            "socialize": (100.0 - self.social) / 100.0,
            "study": (100.0 - self.knowledge) / 100.0,
        }

    def most_urgent_need(self) -> str:
        urgencies = self.get_urgency_scores()
        return max(urgencies, key=lambda k: urgencies[k])
