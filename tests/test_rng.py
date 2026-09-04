"""Unit tests for SeededRNG utility."""

import pytest

from simucity.utils.rng import SeededRNG


def test_seeded_rng_reproducibility() -> None:
    rng1 = SeededRNG(seed=123)
    rng2 = SeededRNG(seed=123)

    floats1 = [rng1.random() for _ in range(10)]
    floats2 = [rng2.random() for _ in range(10)]
    assert floats1 == floats2

    ints1 = [rng1.randint(1, 100) for _ in range(10)]
    ints2 = [rng2.randint(1, 100) for _ in range(10)]
    assert ints1 == ints2


def test_seeded_rng_methods() -> None:
    rng = SeededRNG(seed=42)
    assert rng.seed == 42

    u = rng.uniform(5.0, 10.0)
    assert 5.0 <= u <= 10.0

    items = ["apple", "banana", "cherry"]
    choice = rng.choice(items)
    assert choice in items

    sampled = rng.sample(items, 2)
    assert len(sampled) == 2
    assert set(sampled).issubset(set(items))

    deck = [1, 2, 3, 4, 5]
    rng.shuffle(deck)
    assert set(deck) == {1, 2, 3, 4, 5}

    g = rng.gauss(0.0, 1.0)
    assert isinstance(g, float)

    # Reseed
    rng.reseed(999)
    assert rng.seed == 999

    with pytest.raises(IndexError):
        rng.choice([])
