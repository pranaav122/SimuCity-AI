"""World state models and immutable snapshot representations."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStateSnapshot(BaseModel):
    """Snapshot of an individual agent's vital physical metrics at a tick."""

    agent_id: str
    location_id: str
    money: float = 100.0
    energy: float = 100.0   # [0-100], 100 is fully rested
    hunger: float = 0.0     # [0-100], 100 is starving
    stress: float = 0.0     # [0-100], 100 is maximum stress
    social: float = 50.0    # [0-100], 0 is isolated, 100 is fully connected
    knowledge: float = 10.0 # [0-100], cumulative academic learning
    gpa: float = 3.5        # [0.0 - 4.0]
    current_activity: str = "idle"


class WorldStateSnapshot(BaseModel):
    """Immutable snapshot of the entire world state at a discrete simulation tick."""

    tick: int
    day: int
    hour: int
    minute: int
    time_str: str
    day_of_week: str
    weather: str = "Clear"
    campus_alert_level: str = "Normal"
    location_occupancies: Dict[str, List[str]] = Field(default_factory=dict)
    price_multipliers: Dict[str, float] = Field(default_factory=dict)
    active_event_ids: List[str] = Field(default_factory=list)
    agent_states: Dict[str, AgentStateSnapshot] = Field(default_factory=dict)
