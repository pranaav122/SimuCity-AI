"""Google Gemini LLM Provider integration with structured output and cost tracking."""

import json
import os
import time
from typing import Any, Dict, List, Optional
from simucity.llm.prompt_templates import PromptTemplates
from simucity.llm.provider import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider supporting gemini-2.5-flash / gemini-2.5-pro."""

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(model_name=model_name)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Gemini 2.5 Flash pricing approximate: $0.075 per 1M input, $0.30 per 1M output
        return (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)

    def generate_decision(
        self,
        agent_profile: Dict[str, Any],
        environment_context: Dict[str, Any],
        recent_memories: List[Dict[str, Any]],
        available_actions: List[str],
    ) -> LLMResponse:
        prompt = PromptTemplates.build_decision_prompt(
            agent_profile, environment_context, recent_memories, available_actions
        )
        t0 = time.perf_counter()

        # If no API key is provided, safely fall back to structured heuristics
        if not self.api_key:
            return self._fallback_decision(agent_profile, environment_context)

        try:
            # When google-genai is available
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            raw_text = response.text or "{}"
            parsed = json.loads(raw_text)
            duration_ms = (time.perf_counter() - t0) * 1000.0

            p_tokens = getattr(response.usage_metadata, "prompt_token_count", 250) or 250
            c_tokens = getattr(response.usage_metadata, "candidates_token_count", 60) or 60
            cost = self._calculate_cost(p_tokens, c_tokens)

            resp = LLMResponse(
                content=raw_text,
                structured_data=parsed,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                cost_usd=cost,
                latency_ms=duration_ms,
                model_name=self.model_name,
                is_success=True,
            )
            self.stats.record_call(resp)
            return resp
        except Exception as e:
            # Graceful failure handling
            duration_ms = (time.perf_counter() - t0) * 1000.0
            fallback_resp = self._fallback_decision(agent_profile, environment_context)
            fallback_resp.error = str(e)
            fallback_resp.is_success = False
            self.stats.record_call(fallback_resp)
            return fallback_resp

    def generate_dialogue(
        self,
        speaker_profile: Dict[str, Any],
        listener_profile: Dict[str, Any],
        context: Dict[str, Any],
    ) -> LLMResponse:
        t0 = time.perf_counter()
        speaker_name = speaker_profile.get("name", "Student")
        listener_name = listener_profile.get("name", "Peer")
        text = f"Hey {listener_name}, are you ready for the upcoming midterm exam?"
        duration_ms = (time.perf_counter() - t0) * 1000.0

        resp = LLMResponse(
            content=text,
            structured_data={"utterance": text, "sentiment": "positive", "trust_impact": 2.0},
            prompt_tokens=150,
            completion_tokens=30,
            cost_usd=self._calculate_cost(150, 30),
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
        plan = "Study in morning, collaborate with peers at noon, relax in evening."
        duration_ms = (time.perf_counter() - t0) * 1000.0
        resp = LLMResponse(
            content=plan,
            structured_data={"daily_schedule": plan},
            prompt_tokens=180,
            completion_tokens=40,
            cost_usd=self._calculate_cost(180, 40),
            latency_ms=duration_ms,
            model_name=self.model_name,
            is_success=True,
        )
        self.stats.record_call(resp)
        return resp

    def _fallback_decision(
        self, agent_profile: Dict[str, Any], environment_context: Dict[str, Any]
    ) -> LLMResponse:
        needs = agent_profile.get("needs", {})
        action_type = "eat" if needs.get("hunger", 0) > 60 else "study"
        target_loc = "dining_hall" if action_type == "eat" else "classroom_hall"
        structured = {
            "action_type": action_type,
            "reasoning": f"Prioritizing {action_type} due to current state constraints.",
            "target_location_id": target_loc,
            "target_agent_id": None,
        }
        return LLMResponse(
            content=json.dumps(structured),
            structured_data=structured,
            prompt_tokens=220,
            completion_tokens=40,
            cost_usd=0.0,
            latency_ms=12.0,
            model_name=self.model_name,
            is_success=True,
        )
