"""Campus-wide social network graph and emergent group community detector."""

from typing import Any

import networkx as nx


class SocialGraph:
    """Manages global relationship network, emergent group detection, and topological metrics."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    def add_agent(self, agent_id: str) -> None:
        if not self._graph.has_node(agent_id):
            self._graph.add_node(agent_id)

    def update_edge(
        self,
        from_agent_id: str,
        to_agent_id: str,
        trust: float,
        friendship: float,
        hostility: float,
    ) -> None:
        self.add_agent(from_agent_id)
        self.add_agent(to_agent_id)
        self._graph.add_edge(
            from_agent_id,
            to_agent_id,
            trust=trust,
            friendship=friendship,
            hostility=hostility,
            weight=friendship + trust - hostility,
        )

    def detect_emergent_groups(self, friendship_threshold: float = 20.0) -> list[dict[str, Any]]:
        """Identifies organic friend clusters and study groups based on reciprocal positive relations."""
        # Create undirected sub-graph of positive bonds
        undirected_pos = nx.Graph()
        for u in self._graph.nodes():
            undirected_pos.add_node(u)

        for u, v, data in self._graph.edges(data=True):
            if self._graph.has_edge(v, u):
                # Reciprocal edge check
                v_data = self._graph[v][u]
                avg_friendship = (data.get("friendship", 0) + v_data.get("friendship", 0)) / 2.0
                if avg_friendship >= friendship_threshold:
                    undirected_pos.add_edge(u, v, weight=avg_friendship)

        # Detect communities using connected components or Louvain/greedy modularity
        groups = []
        components = [c for c in nx.connected_components(undirected_pos) if len(c) >= 2]

        for idx, comp in enumerate(components):
            members = sorted(list(comp))
            # Calculate internal group cohesion
            subg = undirected_pos.subgraph(comp)
            cohesion = float(nx.density(subg))
            groups.append(
                {
                    "group_id": f"group_{idx + 1}",
                    "members": members,
                    "size": len(members),
                    "cohesion": round(cohesion, 2),
                    "type": "Study Circle / Alliance" if len(members) <= 4 else "Social Club",
                }
            )

        return groups

    def get_metrics(self) -> dict[str, float]:
        """Calculates global social topology metrics."""
        num_nodes = self._graph.number_of_nodes()
        if num_nodes <= 1:
            return {
                "density": 0.0,
                "cooperation_index": 0.0,
                "conflict_index": 0.0,
                "clustering_coefficient": 0.0,
            }

        density = nx.density(self._graph)

        edges = self._graph.edges(data=True)
        if not edges:
            return {
                "density": round(float(density), 3),
                "cooperation_index": 0.0,
                "conflict_index": 0.0,
                "clustering_coefficient": 0.0,
            }

        total_trust = sum(d.get("trust", 0.0) for _, _, d in edges)
        total_hostility = sum(d.get("hostility", 0.0) for _, _, d in edges)
        num_edges = max(1, len(edges))

        # Convert to undirected for clustering
        undir = self._graph.to_undirected()
        clustering = nx.average_clustering(undir)

        return {
            "density": round(float(density), 3),
            "cooperation_index": round(total_trust / num_edges, 2),
            "conflict_index": round(total_hostility / num_edges, 2),
            "clustering_coefficient": round(float(clustering), 3),
        }

    def to_network_data(self) -> dict[str, Any]:
        """Serializes nodes and links for frontend D3 / Canvas visualization."""
        nodes = [{"id": n, "label": n} for n in self._graph.nodes()]
        links = []
        for u, v, d in self._graph.edges(data=True):
            links.append(
                {
                    "source": u,
                    "target": v,
                    "trust": d.get("trust", 0),
                    "friendship": d.get("friendship", 0),
                    "hostility": d.get("hostility", 0),
                    "weight": d.get("weight", 0),
                }
            )
        return {"nodes": nodes, "links": links}
