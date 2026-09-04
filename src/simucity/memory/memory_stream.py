"""Memory stream managing short-term buffering and long-term retrieval."""

import uuid
from typing import List, Optional
from simucity.memory.memory_item import MemoryItem


class MemoryStream:
    """Agent memory stream managing episodic experiences, recency decay, and semantic retrieval."""

    def __init__(self, short_term_capacity: int = 15) -> None:
        self.short_term_capacity = short_term_capacity
        self.short_term_buffer: List[MemoryItem] = []
        self.long_term_store: List[MemoryItem] = []

    def add_memory(
        self,
        description: str,
        importance: int,
        tick: int,
        timestamp_str: str,
        emotional_valence: float = 0.0,
        involved_agent_ids: Optional[List[str]] = None,
        location_id: Optional[str] = None,
    ) -> MemoryItem:
        """Records a new episodic memory item."""
        mem = MemoryItem(
            id=f"mem_{uuid.uuid4().hex[:8]}",
            tick=tick,
            timestamp_str=timestamp_str,
            description=description,
            importance=max(1, min(10, importance)),
            emotional_valence=max(-1.0, min(1.0, emotional_valence)),
            involved_agent_ids=involved_agent_ids or [],
            location_id=location_id,
            last_accessed_tick=tick,
        )

        self.short_term_buffer.append(mem)
        self.long_term_store.append(mem)

        if len(self.short_term_buffer) > self.short_term_capacity:
            self.short_term_buffer.pop(0)

        return mem

    def retrieve(
        self,
        query: str,
        current_tick: int,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """Retrieves top-k most relevant memories based on composite recency, importance, and query relevance."""
        if not self.long_term_store:
            return []

        query_keywords = [w.strip() for w in query.split() if len(w.strip()) > 2]

        scored_memories = [
            (mem.compute_retrieval_score(current_tick, query_keywords), mem)
            for mem in self.long_term_store
        ]

        # Sort descending by score
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        selected = [mem for _, mem in scored_memories[:top_k]]
        for mem in selected:
            mem.last_accessed_tick = current_tick

        return selected

    def get_recent_summary(self, n: int = 5) -> str:
        """Returns concise textual summary of recent events."""
        recent = self.short_term_buffer[-n:] if self.short_term_buffer else []
        if not recent:
            return "No recent memories recorded."
        return "\n".join(f"- [{m.timestamp_str}] {m.description}" for m in recent)
