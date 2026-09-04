"""Unit tests for MemoryItem and MemoryStream."""

from simucity.memory.memory_stream import MemoryStream


def test_memory_stream_buffering() -> None:
    stream = MemoryStream(short_term_capacity=3)
    stream.add_memory("Event 1", importance=2, tick=0, timestamp_str="08:00")
    stream.add_memory("Event 2", importance=4, tick=1, timestamp_str="08:15")
    stream.add_memory("Event 3", importance=6, tick=2, timestamp_str="08:30")
    assert len(stream.short_term_buffer) == 3

    # Adding 4th item should pop the oldest from short term buffer, but keep in long term
    stream.add_memory("Event 4", importance=8, tick=3, timestamp_str="08:45")
    assert len(stream.short_term_buffer) == 3
    assert stream.short_term_buffer[0].description == "Event 2"
    assert len(stream.long_term_store) == 4


def test_memory_ranked_retrieval() -> None:
    stream = MemoryStream()
    stream.add_memory("Ate breakfast alone", importance=2, tick=10, timestamp_str="08:00")
    stream.add_memory("Alice transferred $50 to help me during financial crisis", importance=10, tick=20, timestamp_str="10:00", involved_agent_ids=["Alice"])
    stream.add_memory("Studied in library", importance=3, tick=25, timestamp_str="11:00")

    # Query with Alice and crisis keywords
    results = stream.retrieve("Alice crisis money help", current_tick=30, top_k=1)
    assert len(results) == 1
    assert "Alice" in results[0].involved_agent_ids
    assert results[0].importance == 10
