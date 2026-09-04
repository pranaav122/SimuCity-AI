"""Unit tests for SimuAgent, Personalities, Needs, and Goals."""

import pytest
from simucity.agents.agent import SimuAgent
from simucity.agents.goals import AgentGoal, GoalCategory, create_default_goals
from simucity.agents.needs import AgentNeeds
from simucity.agents.personality import Personality
from simucity.core.actions import ActionType
from simucity.core.clock import SimulationClock
from simucity.core.environment import CampusEnvironment
from simucity.core.world_state import AgentStateSnapshot, WorldStateSnapshot


def test_personality_archetypes() -> None:
    introvert = Personality.scholarly_introvert()
    assert introvert.extroversion < 0.3
    assert introvert.ambition >= 0.8

    socialite = Personality.social_butterfly()
    assert socialite.extroversion > 0.8
    assert socialite.cooperation > 0.7

    entrepreneur = Personality.ambitious_entrepreneur()
    assert entrepreneur.ambition >= 0.9

    thrifty = Personality.thrifty_slacker()
    assert thrifty.ambition <= 0.3


def test_agent_needs_and_urgency() -> None:
    needs = AgentNeeds(hunger=80.0, energy=20.0, stress=15.0)
    urgencies = needs.get_urgency_scores()
    assert urgencies["eat"] == 0.8
    assert urgencies["sleep"] == 0.8
    assert needs.most_urgent_need() in ("eat", "sleep")


def test_agent_goals_progress() -> None:
    goals = create_default_goals("scholar")
    gpa_goal = next(g for g in goals if g.id == "g_gpa")
    assert not gpa_goal.is_completed

    gpa_goal.update_progress(3.9)
    assert gpa_goal.is_completed
    assert gpa_goal.current_progress == 1.0


def test_simu_agent_heuristic_action_selection() -> None:
    agent = SimuAgent(
        agent_id="agent_alice",
        name="Alice",
        archetype="scholar",
        needs=AgentNeeds(hunger=80.0, energy=80.0),
    )
    clock = SimulationClock(start_day=1, start_hour=12, start_minute=0)
    env = CampusEnvironment.create_default_campus()

    # Agent in dorm with hunger 80 should propose moving to dining hall
    snapshot = WorldStateSnapshot(
        tick=0, day=1, hour=12, minute=0, time_str="12:00", day_of_week="Monday",
        agent_states={"agent_alice": AgentStateSnapshot(agent_id="agent_alice", location_id="dorm_north", money=50.0, hunger=80.0, energy=80.0)}
    )

    action = agent.evaluate_heuristic_action(snapshot, clock, env)
    assert action.action_type == ActionType.MOVE
    assert action.target_location_id == "dining_hall"

    # Agent already in dining hall with hunger 80 should propose eating
    snapshot.agent_states["agent_alice"].location_id = "dining_hall"
    action_eat = agent.evaluate_heuristic_action(snapshot, clock, env)
    assert action_eat.action_type == ActionType.EAT
