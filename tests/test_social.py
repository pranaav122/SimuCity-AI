"""Unit tests for Relationships and SocialGraph."""

from simucity.social.relationship import Relationship
from simucity.social.social_network import SocialGraph


def test_relationship_modification() -> None:
    rel = Relationship(target_agent_id="bob", trust=0.0, friendship=10.0)
    rel.modify(trust_delta=20.0, friendship_delta=15.0, hostility_delta=0.0, current_tick=5)
    assert rel.trust == 20.0
    assert rel.friendship == 25.0
    assert rel.interaction_count == 1
    assert rel.last_interaction_tick == 5


def test_social_graph_group_detection_and_metrics() -> None:
    graph = SocialGraph()
    # Mutual high-friendship cluster: Alice, Bob, Charlie
    graph.update_edge("alice", "bob", trust=40, friendship=50, hostility=0)
    graph.update_edge("bob", "alice", trust=40, friendship=50, hostility=0)
    graph.update_edge("alice", "charlie", trust=30, friendship=40, hostility=0)
    graph.update_edge("charlie", "alice", trust=30, friendship=40, hostility=0)

    groups = graph.detect_emergent_groups(friendship_threshold=20.0)
    assert len(groups) >= 1
    assert set(groups[0]["members"]) == {"alice", "bob", "charlie"}

    metrics = graph.get_metrics()
    assert metrics["density"] > 0.0
    assert metrics["cooperation_index"] > 0.0
