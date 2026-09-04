"""Anthropic Claude LLM Provider integration with structured reasoning and error handling."""

import json
import os
import time
from typing import Any, Dict, List, Optional
from simucity.llm.prompt_templates import PromptTemplates
from simucity.llm.provider import LLMProvider, LLMResponse

_MISSING_KEY_MSG = (
    "ANTHROPIC_API_KEY environment variable is not set. "
    "Set it with: export ANTHROPIC_API_KEY=sk-ant-... "
    "or add it to a .env file. "
    "Use model='mock' to run without an API key."
)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude Provider supporting claude-3-5-sonnet / claude-3-haiku.

    Requires ANTHROPIC_API_KEY environment variable.
    Raises EnvironmentError on construction if the key is absent.
    """

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(model_name=model_name)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not self.api_key:
            raise EnvironmentError(_MISSING_KEY_MSG)

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Claude 3.5 Sonnet pricing: $3.00/1M input, $15.00/1M output."""
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
            with urllib.request.urlopen(req, timeout=30) as resp_stream:
                resp_json = json.loads(resp_stream.read().decode("utf-8"))
                text_content = resp_json.get("content", [{}])[0].get("text", "{}")
                try:
                    parsed = json.loads(text_content)
                except json.JSONDecodeError:
                    # Claude may return plain text; wrap it
                    parsed = {"action_type": "study", "reasoning": text_content}
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
            resp = LLMResponse(
                content="",
                structured_data=None,
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=0.0,
                latency_ms=duration_ms,
                model_name=self.model_name,
                is_success=False,
                error=str(e),
            )
            self.stats.record_call(resp)
            return resp

    def generate_dialogue(
        self,
        speaker_profile: Dict[str, Any],
        listener_profile: Dict[str, Any],
        context: Dict[str, Any],
    ) -> LLMResponse:
        speaker_name = speaker_profile.get("name", "Student")
        listener_name = listener_profile.get("name", "Peer")
        t0 = time.perf_counter()

        prompt = (
            f"You are {speaker_name} speaking to {listener_name} on campus. "
            f"Context: {json.dumps(context)}. "
            "Generate a single natural dialogue utterance. Respond with just the spoken text."
        )
        try:
            import urllib.request
            req_data = json.dumps({
                "model": self.model_name,
                "max_tokens": 100,
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
            with urllib.request.urlopen(req, timeout=30) as resp_stream:
                resp_json = json.loads(resp_stream.read().decode("utf-8"))
                text = resp_json.get("content", [{}])[0].get("text", "Hi!")
                usage = resp_json.get("usage", {})
                p_tokens = usage.get("input_tokens", 160)
                c_tokens = usage.get("output_tokens", 30)
                duration_ms = (time.perf_counter() - t0) * 1000.0
                resp = LLMResponse(
                    content=text,
                    structured_data={"utterance": text, "speaker": speaker_name, "listener": listener_name},
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    cost_usd=self._calculate_cost(p_tokens, c_tokens),
                    latency_ms=duration_ms,
                    model_name=self.model_name,
                    is_success=True,
                )
                self.stats.record_call(resp)
                return resp
        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            resp = LLMResponse(
                content="", structured_data=None, prompt_tokens=0, completion_tokens=0,
                cost_usd=0.0, latency_ms=duration_ms, model_name=self.model_name,
                is_success=False, error=str(e),
            )
            self.stats.record_call(resp)
            return resp

    def generate_plan(
        self,
        agent_profile: Dict[str, Any],
        world_context: Dict[str, Any],
    ) -> LLMResponse:
        t0 = time.perf_counter()
        name = agent_profile.get("name", "Student")
        prompt = (
            f"You are {name}, a university student. Given your current state: "
            f"{json.dumps(agent_profile.get('needs', {}))} "
            "Generate a brief daily schedule plan in one sentence."
        )
        try:
            import urllib.request
            req_data = json.dumps({
                "model": self.model_name,
                "max_tokens": 150,
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
            with urllib.request.urlopen(req, timeout=30) as resp_stream:
                resp_json = json.loads(resp_stream.read().decode("utf-8"))
                plan = resp_json.get("content", [{}])[0].get("text", "Study and attend classes.")
                usage = resp_json.get("usage", {})
                p_tokens = usage.get("input_tokens", 200)
                c_tokens = usage.get("output_tokens", 40)
                duration_ms = (time.perf_counter() - t0) * 1000.0
                resp = LLMResponse(
                    content=plan,
                    structured_data={"daily_schedule": plan},
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    cost_usd=self._calculate_cost(p_tokens, c_tokens),
                    latency_ms=duration_ms,
                    model_name=self.model_name,
                    is_success=True,
                )
                self.stats.record_call(resp)
                return resp
        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000.0
            resp = LLMResponse(
                content="", structured_data=None, prompt_tokens=0, completion_tokens=0,
                cost_usd=0.0, latency_ms=duration_ms, model_name=self.model_name,
                is_success=False, error=str(e),
            )
            self.stats.record_call(resp)
            return resp
