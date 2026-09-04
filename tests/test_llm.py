"""Tests for LLM providers, information propagation, and event system."""

import pytest

from simucity.events.event import SimulationEvent
from simucity.events.event_manager import EventManager
from simucity.information.info_propagator import InformationLedger
from simucity.llm.mock_provider import MockLLMProvider

# ── Information Propagation ────────────────────────────────────────────────────


def test_information_propagation() -> None:
    ledger = InformationLedger()
    info = ledger.publish_info(
        info_id="info_rumor",
        topic="Midterm Exam Difficulty",
        content="Exam will be extremely hard.",
        source="StudentA",
        origin_tick=0,
    )
    assert info.reach == 1

    conf = info.transmit(sender_id="StudentA", receiver_id="StudentB", tick=2, sender_trust=50.0)
    assert info.reach == 2
    assert info.cascade_depth == 1
    assert conf >= 0.0  # Confidence depends on trust; just verify it's a valid float


# ── Event Manager ─────────────────────────────────────────────────────────────


def test_event_manager_lifecycle(default_engine) -> None:  # type: ignore[no-untyped-def]
    manager = EventManager()
    event = SimulationEvent.cafeteria_price_shock(trigger_tick=4)
    manager.schedule_event(event)

    triggered = manager.tick(0, default_engine)
    assert len(triggered) == 0
    assert not event.is_active

    triggered_4 = manager.tick(4, default_engine)
    assert len(triggered_4) == 1
    assert event.is_active
    assert default_engine.price_multipliers["dining_hall"] == 1.25


# ── Mock Provider ─────────────────────────────────────────────────────────────


def test_mock_llm_provider_telemetry() -> None:
    provider = MockLLMProvider()
    resp = provider.generate_decision(
        agent_profile={"needs": {"hunger": 80, "energy": 90}, "personality": {"extroversion": 0.5}},
        environment_context={"is_class_hours": False, "co_located_agents": []},
        recent_memories=[],
        available_actions=["eat", "sleep", "study"],
    )
    assert resp.is_success
    assert resp.structured_data is not None
    assert resp.structured_data["action_type"] == "eat"
    assert provider.stats.total_calls == 1
    assert provider.stats.total_prompt_tokens > 0


def test_mock_provider_is_deterministic() -> None:
    """Same inputs must produce identical decisions across calls (no RNG in mock)."""
    provider = MockLLMProvider()
    profile = {"needs": {"hunger": 20, "energy": 80}, "personality": {"extroversion": 0.3}}
    ctx = {"is_class_hours": True, "co_located_agents": []}
    resp1 = provider.generate_decision(profile, ctx, [], ["study", "attend_class"])
    resp2 = provider.generate_decision(profile, ctx, [], ["study", "attend_class"])
    assert resp1.structured_data is not None
    assert resp2.structured_data is not None
    assert resp1.structured_data["action_type"] == resp2.structured_data["action_type"]


def test_mock_provider_generates_plan() -> None:
    provider = MockLLMProvider()
    resp = provider.generate_plan(agent_profile={"name": "Alice"}, world_context={})
    assert resp.is_success
    assert resp.content != ""
    assert resp.structured_data is not None
    assert "daily_schedule" in resp.structured_data


def test_mock_provider_generates_dialogue() -> None:
    provider = MockLLMProvider()
    resp = provider.generate_dialogue(
        speaker_profile={"name": "Alice"},
        listener_profile={"name": "Bob"},
        context={},
    )
    assert resp.is_success
    assert "Bob" in resp.content or "Bob" in str(resp.structured_data)


# ── Provider key validation ───────────────────────────────────────────────────


def test_claude_provider_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """ClaudeProvider must raise EnvironmentError when ANTHROPIC_API_KEY is absent."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from simucity.llm.claude_provider import ClaudeProvider  # noqa: PLC0415

    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        ClaudeProvider()


def test_gemini_provider_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GeminiProvider must raise EnvironmentError when GEMINI_API_KEY is absent."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    from simucity.llm.gemini_provider import GeminiProvider  # noqa: PLC0415

    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        GeminiProvider()


def test_mock_provider_stats_accumulate() -> None:
    """Stats must accumulate correctly over multiple calls."""
    provider = MockLLMProvider()
    for _ in range(5):
        provider.generate_decision(
            agent_profile={
                "needs": {"hunger": 10, "energy": 80},
                "personality": {"extroversion": 0.5},
            },
            environment_context={"is_class_hours": False, "co_located_agents": []},
            recent_memories=[],
            available_actions=["study"],
        )
    assert provider.stats.total_calls == 5
    assert provider.stats.successful_calls == 5
    assert provider.stats.total_prompt_tokens == 5 * 180  # 180 per call in mock


# ── LLM wired into ExperimentRunner ──────────────────────────────────────────


def test_mock_experiment_runner_does_not_call_llm() -> None:
    """Mock mode must use heuristics only — llm_provider.stats.total_calls stays 0."""
    from simucity.experiments.experiment_runner import (  # noqa: PLC0415
        ExperimentConfig,
        ExperimentRunner,
    )

    cfg = ExperimentConfig(
        experiment_id="test_no_llm_calls",
        number_of_agents=2,
        simulation_days=1,
        model="mock",
        seed=99,
    )
    runner = ExperimentRunner(cfg)
    result = runner.run()

    # In mock/heuristic mode, the llm_provider (MockLLMProvider) is never called
    # because _use_llm is False — the heuristic pipeline is used directly
    assert result.total_ticks == 96
    assert result.final_metrics is not None
    # total_tokens will be 0 since we don't call the mock's generate_decision
    assert result.total_tokens == 0
