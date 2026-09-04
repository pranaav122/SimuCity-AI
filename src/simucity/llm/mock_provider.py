"""Mock LLM Provider for high-speed, zero-cost deterministic simulation & tests."""

import time
from typing import Any, Dict, List
from simucity.llm.provider import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM Provider simulating structured LLM responses."""

    def __init__(self, model_name: str = "simucity-mock-v1") -> None:
        super().__init__(model_name=model_name)

    def generate_decision(
        self,
        agent_profile: Dict[str, Any],
        environment_context: Dict[str, Any],
        recent_memories: List[Dict[str, Any]],
        available_actions: List[str],
    ) -> LLMResponse:
        t0 = time.perf_counter()

        needs = agent_profile.get("needs", {})
        hunger = needs.get("hunger", 0)
        energy = needs.get("energy", 100)
        is_class_hours = environment_context.get("is_class_hours", False)
        co_located = environment_context.get("co_located_agents", [])

        # Heuristic decision logic
        if hunger > 60:
            chosen = "eat"
            reason = "My hunger level is high, so I need to eat at the cafeteria."
        elif energy < 25:
            chosen = "sleep"
            reason = "My energy is depleted, heading to dormitory to rest."
        elif is_class_hours and energy >= 30:
            chosen = "attend_class"
            reason = "Class is in session, I must attend lecture."
        elif co_located and agent_profile.get("personality", {}).get("extroversion", 0.5) > 0.6:
            chosen = "socialize"
            reason = f"Talking with {co_located[0]} to strengthen social connection."
        else:
            chosen = "study"
            reason = "Studying to improve academic GPA and knowledge."

        duration_ms = (time.perf_counter() - t0) * 1000.0

        structured = {
            "action_type": chosen,
            "reasoning": reason,
            "target_location_id": "dining_hall" if chosen == "eat" else ("dorm_north" if chosen == "sleep" else "classroom_hall"),
            "target_agent_id": co_located[0] if (chosen == "socialize" and co_located) else None,
        }

        resp = LLMResponse(
            content=f"Decision: {chosen}. {reason}",
            structured_data=structured,
            prompt_tokens=180,
            completion_tokens=45,
            cost_usd=0.0,
            latency_ms=duration_ms,
            model_name=self.model_name,
            is_success=True,
        )
        self.stats.record_call(resp)
        return resp

    def generate_dialogue(
        self,
        speaker_profile: Dict[str, Any],
        listener_profile: Dict[str, Any],
        context: Dict[str, Any],
    ) -> LLMResponse:
        t0 = time.perf_counter()
        speaker_name = speaker_profile.get("name", "Student")
        listener_name = listener_profile.get("name", "Peer")

        dialogue = f"Hey {listener_name}! How are your classes going this week?"
        duration_ms = (time.perf_counter() - t0) * 1000.0

        resp = LLMResponse(
            content=dialogue,
            structured_data={"utterance": dialogue, "speaker": speaker_name, "listener": listener_name},
            prompt_tokens=120,
            completion_tokens=25,
            cost_usd=0.0,
            latency_ms=duration_ms,
            model_name=self.model_name,
            is_success=True,
        )
        self.stats.record_call(resp)
        return resp

    def generate_plan(
        self,
        agent_profile: Dict[str, Any],
        world_context: Dict[str, Any],
    ) -> LLMResponse:
        t0 = time.perf_counter()
        plan_str = "08:00 Attend lectures; 12:00 Lunch at cafeteria; 14:00 Library study; 18:00 Recreation & social; 22:00 Sleep."
        duration_ms = (time.perf_counter() - t0) * 1000.0

        resp = LLMResponse(
            content=plan_str,
            structured_data={"daily_schedule": plan_str},
            prompt_tokens=150,
            completion_tokens=35,
            cost_usd=0.0,
            latency_ms=duration_ms,
            model_name=self.model_name,
            is_success=True,
        )
        self.stats.record_call(resp)
        return resp
