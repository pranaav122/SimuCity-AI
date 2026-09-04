"""LLM Provider abstraction and telemetry interfaces."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Encapsulates the response from an LLM call with complete telemetry."""

    content: str = ""
    structured_data: dict[str, Any] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    model_name: str = "mock"
    is_success: bool = True
    error: str | None = None


class ProviderUsageStats(BaseModel):
    """Tracks aggregate token consumption, latency, and cost for an experiment."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0

    @property
    def average_latency_ms(self) -> float:
        return (self.total_latency_ms / self.total_calls) if self.total_calls > 0 else 0.0

    def record_call(self, response: LLMResponse) -> None:
        self.total_calls += 1
        if response.is_success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        self.total_prompt_tokens += response.prompt_tokens
        self.total_completion_tokens += response.completion_tokens
        self.total_cost_usd += response.cost_usd
        self.total_latency_ms += response.latency_ms


class LLMProvider(ABC):
    """Abstract interface for all model providers (Claude, Gemini, Mock, Local)."""

    def __init__(self, model_name: str = "unknown") -> None:
        self.model_name = model_name
        self.stats = ProviderUsageStats()

    @abstractmethod
    def generate_decision(
        self,
        agent_profile: dict[str, Any],
        environment_context: dict[str, Any],
        recent_memories: list[dict[str, Any]],
        available_actions: list[str],
    ) -> LLMResponse:
        """Generates the next action decision for an agent given its internal state and surroundings."""
        pass

    @abstractmethod
    def generate_dialogue(
        self,
        speaker_profile: dict[str, Any],
        listener_profile: dict[str, Any],
        context: dict[str, Any],
    ) -> LLMResponse:
        """Generates conversational dialogue between two interacting agents."""
        pass

    @abstractmethod
    def generate_plan(
        self,
        agent_profile: dict[str, Any],
        world_context: dict[str, Any],
    ) -> LLMResponse:
        """Generates a high-level daily routine or strategic plan."""
        pass
