"""Personality profiles and psychological traits for autonomous agents."""

from pydantic import BaseModel, Field


class Personality(BaseModel):
    """Seven-dimensional personality model influencing agent decisions and social dynamics.

    All trait scores are normalized in [0.0, 1.0].
    """

    extroversion: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Propensity to socialize and initiate conversations",
    )
    risk_tolerance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Willingness to spend money or take non-standard actions",
    )
    cooperation: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Tendency to share resources, help others, and join groups",
    )
    ambition: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Drive for high academic GPA and career achievement",
    )
    patience: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Tolerance for low immediate rewards and delayed gratification",
    )
    trust: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Initial baseline trust towards unfamiliar agents and rumors",
    )
    curiosity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Inclination to explore new locations and investigate information",
    )

    def to_dict(self) -> dict[str, float]:
        return {
            "extroversion": round(self.extroversion, 2),
            "risk_tolerance": round(self.risk_tolerance, 2),
            "cooperation": round(self.cooperation, 2),
            "ambition": round(self.ambition, 2),
            "patience": round(self.patience, 2),
            "trust": round(self.trust, 2),
            "curiosity": round(self.curiosity, 2),
        }

    @classmethod
    def scholarly_introvert(cls) -> "Personality":
        return cls(
            extroversion=0.2,
            risk_tolerance=0.2,
            cooperation=0.6,
            ambition=0.9,
            patience=0.85,
            trust=0.6,
            curiosity=0.8,
        )

    @classmethod
    def social_butterfly(cls) -> "Personality":
        return cls(
            extroversion=0.95,
            risk_tolerance=0.7,
            cooperation=0.85,
            ambition=0.4,
            patience=0.4,
            trust=0.8,
            curiosity=0.75,
        )

    @classmethod
    def ambitious_entrepreneur(cls) -> "Personality":
        return cls(
            extroversion=0.75,
            risk_tolerance=0.85,
            cooperation=0.5,
            ambition=0.95,
            patience=0.6,
            trust=0.4,
            curiosity=0.9,
        )

    @classmethod
    def thrifty_slacker(cls) -> "Personality":
        return cls(
            extroversion=0.4,
            risk_tolerance=0.1,
            cooperation=0.4,
            ambition=0.2,
            patience=0.7,
            trust=0.5,
            curiosity=0.3,
        )
