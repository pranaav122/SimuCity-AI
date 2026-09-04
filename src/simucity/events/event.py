"""Simulation event definitions and shock triggers."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SimulationEvent(BaseModel):
    """An exogenous or scheduled event that shocks the simulation world."""

    id: str
    title: str
    description: str
    trigger_tick: int
    duration_ticks: int = Field(default=96, description="Duration in ticks (96 ticks = 1 full day)")
    price_multipliers: Dict[str, float] = Field(default_factory=dict, description="Location price modifiers")
    academic_stress_multiplier: float = 1.0
    transport_disabled: bool = False
    rumor_content: Optional[str] = None
    is_active: bool = False

    def is_triggered(self, current_tick: int) -> bool:
        return self.trigger_tick <= current_tick < (self.trigger_tick + self.duration_ticks)

    @classmethod
    def cafeteria_price_shock(cls, trigger_tick: int = 96) -> "SimulationEvent":
        return cls(
            id="event_cafeteria_hike",
            title="Cafeteria Meal Price Surge",
            description="Due to campus supply chain disruption, cafeteria prices increased by 25%.",
            trigger_tick=trigger_tick,
            duration_ticks=96 * 3,
            price_multipliers={"dining_hall": 1.25},
        )

    @classmethod
    def surprise_midterm_exam(cls, trigger_tick: int = 192) -> "SimulationEvent":
        return cls(
            id="event_surprise_exam",
            title="Surprise Midterm Exam Announced",
            description="Professors announce a high-stakes surprise midterm across all departments.",
            trigger_tick=trigger_tick,
            duration_ticks=96 * 2,
            academic_stress_multiplier=1.8,
            rumor_content="Professors are failing anyone with knowledge below 50!",
        )

    @classmethod
    def transit_strike(cls, trigger_tick: int = 288) -> "SimulationEvent":
        return cls(
            id="event_transit_strike",
            title="Campus Shuttle Maintenance Outage",
            description="The central transit plaza shuttles are suspended for emergency repairs.",
            trigger_tick=trigger_tick,
            duration_ticks=96,
            transport_disabled=True,
        )
