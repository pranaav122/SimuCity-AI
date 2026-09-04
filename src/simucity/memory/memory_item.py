"""Individual memory item representation with importance and emotional valence."""

from typing import List, Optional
from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    """An individual episodic memory record."""

    id: str
    tick: int
    timestamp_str: str
    description: str
    importance: int = Field(default=3, ge=1, le=10, description="Significance rating from 1 (trivial) to 10 (life-altering)")
    emotional_valence: float = Field(default=0.0, ge=-1.0, le=1.0, description="Emotional impact: -1.0 (trauma/upset) to +1.0 (ecstatic)")
    involved_agent_ids: List[str] = Field(default_factory=list)
    location_id: Optional[str] = None
    last_accessed_tick: int = 0

    def compute_retrieval_score(self, current_tick: int, query_keywords: List[str], decay_rate: float = 0.99) -> float:
        """Computes the composite retrieval score = Recency + Importance + Relevance."""
        # 1. Recency Decay (exponential)
        ticks_passed = max(0, current_tick - self.tick)
        recency = decay_rate ** ticks_passed

        # 2. Importance [0.1 - 1.0]
        importance_norm = self.importance / 10.0

        # 3. Relevance (Keyword overlap match)
        relevance = 0.0
        if query_keywords:
            desc_words = set(self.description.lower().split())
            matches = sum(1 for kw in query_keywords if kw.lower() in desc_words or any(kw.lower() in a.lower() for a in self.involved_agent_ids))
            relevance = min(1.0, matches / max(1, len(query_keywords)))

        # Weighted combination
        return (0.3 * recency) + (0.35 * importance_norm) + (0.35 * relevance)
