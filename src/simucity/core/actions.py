"""Action models, validation system, and execution outcome structures."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    MOVE = "move"
    WAIT = "wait"
    SLEEP = "sleep"
    REST = "rest"
    EAT = "eat"
    STUDY = "study"
    ATTEND_CLASS = "attend_class"
    WORK = "work"
    PURCHASE_ITEM = "purchase_item"
    SOCIALIZE = "socialize"
    HELP_AGENT = "help_agent"
    REFUSE_HELP = "refuse_help"
    SHARE_INFO = "share_info"
    CHANGE_PLAN = "change_plan"


class ActionStatus(str, Enum):
    SUCCESS = "success"
    REJECTED = "rejected"
    FAILED_PREREQUISITE = "failed_prerequisite"
    CONFLICT = "conflict"


class ProposedAction(BaseModel):
    """An action proposed by an agent (heuristic or LLM reasoning)."""

    agent_id: str = Field(description="ID of the agent initiating the action")
    action_type: ActionType = Field(description="Categorical type of action")
    target_location_id: str | None = Field(default=None, description="Target location for movement")
    target_agent_id: str | None = Field(default=None, description="Target agent for social actions")
    item_id: str | None = Field(default=None, description="Item to purchase or transfer")
    amount: float = Field(default=0.0, ge=0.0, description="Monetary or resource quantity")
    info_payload: dict[str, Any] | None = Field(default=None, description="Data or rumor payload")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary supplemental arguments"
    )


class ActionResult(BaseModel):
    """The deterministic outcome of an executed action evaluated by the simulation engine."""

    action: ProposedAction
    status: ActionStatus
    reason: str | None = None
    tick: int = 0
    energy_delta: float = 0.0
    hunger_delta: float = 0.0
    stress_delta: float = 0.0
    social_delta: float = 0.0
    knowledge_delta: float = 0.0
    money_delta: float = 0.0
    location_changed_to: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
