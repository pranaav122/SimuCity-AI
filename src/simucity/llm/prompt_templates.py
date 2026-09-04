"""Structured prompt builders for LLM decision-making, dialogue, and planning."""

import json
from typing import Any, Dict, List


class PromptTemplates:
    """Standardized prompts enforcing structured JSON output from LLMs."""

    @staticmethod
    def build_decision_prompt(
        agent_profile: Dict[str, Any],
        environment_context: Dict[str, Any],
        recent_memories: List[Dict[str, Any]],
        available_actions: List[str],
    ) -> str:
        return f"""You are simulating an autonomous agent in SimuCity AI.

### AGENT COGNITIVE PROFILE
- ID: {agent_profile.get('id')}
- Name: {agent_profile.get('name')} (Age: {agent_profile.get('age')})
- Personality: {json.dumps(agent_profile.get('personality', {}))}
- Needs (0-100): {json.dumps(agent_profile.get('needs', {}))}
- Active Goals: {json.dumps(agent_profile.get('goals', []))}
- Current Strategic Plan: "{agent_profile.get('current_plan', '')}"

### ENVIRONMENT & TIME
- Current Time: {environment_context.get('time_str')} (Day {environment_context.get('day')}, {environment_context.get('day_of_week')})
- Current Location: {environment_context.get('location_name')} ({environment_context.get('location_id')})
- Money Balance: ${environment_context.get('money', 0):.2f}
- Class In Session: {environment_context.get('is_class_hours')}
- Co-Located Agents: {json.dumps(environment_context.get('co_located_agents', []))}
- Active Campus Events: {json.dumps(environment_context.get('active_events', []))}

### RECENT MEMORIES & RETRIEVED EPISODES
{json.dumps(recent_memories, indent=2)}

### ALLOWED ACTION TYPES
{json.dumps(available_actions)}

### INSTRUCTION
Select the SINGLE best action that advances your goals given your personality, needs, and environmental context.
You MUST output ONLY valid JSON matching this schema:
{{
  "action_type": "move|wait|sleep|rest|eat|study|attend_class|work|purchase_item|socialize|help_agent|share_info",
  "reasoning": "<1-2 sentence internal thought process>",
  "target_location_id": "<valid location id if action is move, else null>",
  "target_agent_id": "<valid co-located agent id if social/help/share_info, else null>",
  "amount": <number if purchase or help_agent, else 0.0>
}}
"""

    @staticmethod
    def build_dialogue_prompt(
        speaker_profile: Dict[str, Any],
        listener_profile: Dict[str, Any],
        context: Dict[str, Any],
    ) -> str:
        return f"""You are generating dialogue between two agents in SimuCity.

Speaker: {speaker_profile.get('name')} (Personality: {json.dumps(speaker_profile.get('personality', {}))})
Listener: {listener_profile.get('name')}
Topic / Context: {json.dumps(context)}

Respond in 1-2 sentences of natural in-character conversational dialogue.
Output JSON:
{{
  "utterance": "<dialogue text>",
  "sentiment": "positive|neutral|negative|confrontational",
  "trust_impact": <-10 to +10>
}}
"""
