"""Dyadic agent relationships and multidimensional social bonds."""

from pydantic import BaseModel, Field


class Relationship(BaseModel):
    """Represents an agent's direct social orientation towards another agent."""

    target_agent_id: str
    trust: float = Field(
        default=0.0,
        ge=-100.0,
        le=100.0,
        description="Trust level: -100 (complete distrust) to +100 (unconditional trust)",
    )
    friendship: float = Field(
        default=0.0,
        ge=-100.0,
        le=100.0,
        description="Affection: -100 (enemies) to +100 (best friends)",
    )
    hostility: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Aggression/animosity: 0 (neutral) to 100 (open feud)",
    )
    respect: float = Field(
        default=10.0, ge=0.0, le=100.0, description="Academic or status respect: 0 to 100"
    )
    familiarity: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Acquaintance level: 0 (stranger) to 100 (lifelong peer)",
    )
    interaction_count: int = 0
    last_interaction_tick: int = 0

    def modify(
        self,
        trust_delta: float = 0.0,
        friendship_delta: float = 0.0,
        hostility_delta: float = 0.0,
        respect_delta: float = 0.0,
        familiarity_delta: float = 1.0,
        current_tick: int = 0,
    ) -> None:
        """Applies deltas with boundary clamping."""
        self.trust = max(-100.0, min(100.0, self.trust + trust_delta))
        self.friendship = max(-100.0, min(100.0, self.friendship + friendship_delta))
        self.hostility = max(0.0, min(100.0, self.hostility + hostility_delta))
        self.respect = max(0.0, min(100.0, self.respect + respect_delta))
        self.familiarity = max(0.0, min(100.0, self.familiarity + familiarity_delta))
        self.interaction_count += 1
        self.last_interaction_tick = current_tick
