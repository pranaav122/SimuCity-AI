"""Unit tests for Information propagation, Events, and LLM Providers."""

from simucity.events.event import SimulationEvent
from simucity.events.event_manager import EventManager
from simucity.information.info_propagator import InformationLedger
from simucity.llm.mock_provider import MockLLMProvider
from simucity.llm.provider import LLMResponse


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

    # Propagate from StudentA to StudentB
    conf = info.transmit(sender_id="StudentA", receiver_id="StudentB", tick=2, sender_trust=50.0)
    assert info.reach == 2
    assert info.cascade_depth == 1
    assert conf > 0.5


def test_event_manager_lifecycle(default_engine) -> None:
    manager = EventManager()
    event = SimulationEvent.cafeteria_price_shock(trigger_tick=4)
    manager.schedule_event(event)

    # Tick 0 - event not active
    triggered = manager.tick(0, default_engine)
    assert len(triggered) == 0
    assert not event.is_active

    # Tick 4 - event triggers
    triggered_4 = manager.tick(4, default_engine)
    assert len(triggered_4) == 1
    assert event.is_active
    assert default_engine.price_multipliers["dining_hall"] == 1.25


def test_mock_llm_provider_telemetry() -> None:
    provider = MockLLMProvider()
    resp = provider.generate_decision(
        agent_profile={"needs": {"hunger": 80, "energy": 90}, "personality": {"extroversion": 0.5}},
        environment_context={"is_class_hours": False, "co_located_agents": []},
        recent_memories=[],
        available_actions=["eat", "sleep", "study"],
    )
    assert resp.is_success
    assert resp.structured_data["action_type"] == "eat"
    assert provider.stats.total_calls == 1
    assert provider.stats.total_prompt_tokens > 0
