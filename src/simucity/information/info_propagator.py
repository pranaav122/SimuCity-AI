"""Information propagation, rumor cascading, and confidence tracking."""

from typing import Any, Dict, List, Set
from pydantic import BaseModel, Field


class Information(BaseModel):
    """A unit of information, rumor, or official announcement circulating on campus."""

    id: str
    topic: str
    content: str
    source: str
    origin_tick: int
    truth_value: bool = True
    initial_confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    recipients: Set[str] = Field(default_factory=set)
    propagation_history: List[Dict[str, Any]] = Field(default_factory=list)

    def transmit(self, sender_id: str, receiver_id: str, tick: int, sender_trust: float = 0.5) -> float:
        """Propagates information to a new agent. Returns updated confidence."""
        self.recipients.add(receiver_id)
        # Receiver confidence depends on sender trust
        received_confidence = min(1.0, self.initial_confidence * max(0.2, (sender_trust + 100.0) / 200.0))
        self.propagation_history.append({
            "sender": sender_id,
            "receiver": receiver_id,
            "tick": tick,
            "confidence": round(received_confidence, 2),
        })
        return received_confidence

    @property
    def reach(self) -> int:
        return len(self.recipients)

    @property
    def cascade_depth(self) -> int:
        return len(self.propagation_history)


class InformationLedger:
    """Manages all information items circulating through the simulation."""

    def __init__(self) -> None:
        self.items: Dict[str, Information] = {}

    def publish_info(
        self,
        info_id: str,
        topic: str,
        content: str,
        source: str,
        origin_tick: int,
        truth_value: bool = True,
        initial_confidence: float = 0.9,
    ) -> Information:
        info = Information(
            id=info_id,
            topic=topic,
            content=content,
            source=source,
            origin_tick=origin_tick,
            truth_value=truth_value,
            initial_confidence=initial_confidence,
            recipients={source} if source != "OFFICIAL" else set(),
        )
        self.items[info_id] = info
        return info

    def get_info(self, info_id: str) -> Information:
        if info_id not in self.items:
            raise KeyError(f"Information '{info_id}' not found.")
        return self.items[info_id]

    def get_summary(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": info.id,
                "topic": info.topic,
                "reach": info.reach,
                "depth": info.cascade_depth,
                "truth_value": info.truth_value,
                "source": info.source,
            }
            for info in self.items.values()
        ]
