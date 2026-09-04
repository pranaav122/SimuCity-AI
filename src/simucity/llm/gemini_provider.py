"""Google Gemini LLM Provider integration with structured output and cost tracking."""

import json
import os
import time
from typing import Any, Dict, List, Optional
from simucity.llm.prompt_templates import PromptTemplates
from simucity.llm.provider import LLMProvider, LLMResponse

_MISSING_KEY_MSG = (
    "GEMINI_API_KEY environment variable is not set. "
    "Set it with: export GEMINI_API_KEY=AIza... "
    "or add it to a .env file. "
    "Use model='mock' to run without an API key."
)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM Provider supporting gemini-2.0-flash.

    Requires GEMINI_API_KEY (or GOOGLE_API_KEY) environment variable.
    Raises EnvironmentError on construction if the key is absent.
    Requires: pip install -e ".[gemini]" (installs google-genai)
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(model_name=model_name)
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY", "").strip()
            or os.environ.get("GOOGLE_API_KEY", "").strip()
        )
        if not self.api_key:
            raise EnvironmentError(_MISSING_KEY_MSG)

    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Gemini 2.0 Flash pricing: $0.075/1M input, $0.30/1M output."""
        return (prompt_tokens * 0.075 / 1_000_000) + (completion_tokens * 0.30 / 1_000_000)

    def _get_client(self) -> Any:
        try:
            from google import genai  # type: ignore[import]
            return genai.Client(api_key=self.api_key)
        except ImportError as exc:
            raise ImportError(
                "google-genai is not installed. "
                "Install it with: pip install -e \".[gemini]\""
            ) from exc

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
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            raw_text = response.text or "{}"
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                parsed = {"action_type": "study", "reasoning": raw_text}
            duration_ms = (time.perf_counter() - t0) * 1000.0

            p_tokens = getattr(response.usage_metadata, "prompt_token_count", None) or 250
            c_tokens = getattr(response.usage_metadata, "candidates_token_count", None) or 60
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
            f"You are {speaker_name} talking to {listener_name} on campus. "
            f"Situation: {json.dumps(context)}. Respond with one natural utterance."
        )
        try:
            client = self._get_client()
            response = client.models.generate_content(model=self.model_name, contents=prompt)
            text = response.text or "Hey, how are you?"
            duration_ms = (time.perf_counter() - t0) * 1000.0
            p_tokens = getattr(response.usage_metadata, "prompt_token_count", None) or 150
            c_tokens = getattr(response.usage_metadata, "candidates_token_count", None) or 30
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
        name = agent_profile.get("name", "Student")
        t0 = time.perf_counter()
        prompt = (
            f"You are {name}, a university student. "
            f"Your current needs: {json.dumps(agent_profile.get('needs', {}))}. "
            "Write a one-sentence daily schedule."
        )
        try:
            client = self._get_client()
            response = client.models.generate_content(model=self.model_name, contents=prompt)
            plan = response.text or "Study in the morning and relax in the evening."
            duration_ms = (time.perf_counter() - t0) * 1000.0
            p_tokens = getattr(response.usage_metadata, "prompt_token_count", None) or 180
            c_tokens = getattr(response.usage_metadata, "candidates_token_count", None) or 40
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
