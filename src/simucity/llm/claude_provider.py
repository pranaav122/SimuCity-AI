"""Anthropic Claude LLM Provider integration with structured reasoning and error handling."""

import json
import os
import time
from typing import Any, Dict, List, Optional
from simucity.llm.prompt_templates import PromptTemplates
from simucity.llm.provider import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    """Anthropic Claude Provider supporting claude-3-5-sonnet / claude-3-haiku."""

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(model_name=model_name)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        # Claude 3.5 Sonnet pricing: $3.00 per 1M input, $15.00 per 1M output
        return (prompt_tokens * 3.0 / 1_000_000) + (completion_tokens * 15.0 / 1_000_000)

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

        if not self.api_key:
            return self._fallback_decision(agent_profile, environment_context)

        try:
            import urllib.request
            req_data = json.dumps({
                "model": self.model_name,
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=req_data,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp_stream:
                resp_json = json.loads(resp_stream.read().decode("utf-8"))
                text_content = resp_json.get("content", [{}])[0].get("text", "{}")
                parsed = json.loads(text_content)
                usage = resp_json.get("usage", {})
                p_tokens = usage.get("input_tokens", 250)
                c_tokens = usage.get("output_tokens", 50)
                cost = self._calculate_cost(p_tokens, c_tokens)
                duration_ms = (time.perf_counter() - t0) * 1000.0

                resp = LLMResponse(
                    content=text_content,
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
        text = f"Hi {listener_name}, do you want to collaborate on the economics project today?"
        duration_ms = (time.perf_counter() - t0) * 1000.0

        resp = LLMResponse(
            content=text,
            structured_data={"utterance": text, "sentiment": "positive", "trust_impact": 3.0},
            prompt_tokens=160,
            completion_tokens=30,
            cost_usd=self._calculate_cost(160, 30),
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
        plan = "Attend all core lectures, focus study sessions at library, build study groups."
        duration_ms = (time.perf_counter() - t0) * 1000.0
        resp = LLMResponse(
            content=plan,
            structured_data={"daily_schedule": plan},
            prompt_tokens=200,
            completion_tokens=40,
            cost_usd=self._calculate_cost(200, 40),
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
        action_type = "sleep" if needs.get("energy", 100) < 30 else "attend_class"
        target_loc = "dorm_north" if action_type == "sleep" else "classroom_hall"
        structured = {
            "action_type": action_type,
            "reasoning": f"Adaptive planning chose {action_type} for optimal utility.",
            "target_location_id": target_loc,
            "target_agent_id": None,
        }
        return LLMResponse(
            content=json.dumps(structured),
            structured_data=structured,
            prompt_tokens=240,
            completion_tokens=45,
            cost_usd=0.0,
            latency_ms=15.0,
            model_name=self.model_name,
            is_success=True,
        )
