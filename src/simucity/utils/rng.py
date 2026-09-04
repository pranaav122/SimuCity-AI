"""Deterministic Random Number Generator wrapper for reproducible simulations."""

import random
from collections.abc import Sequence
from typing import Any, TypeVar

T = TypeVar("T")


class SeededRNG:
    """Encapsulates a deterministic random generator tied to an experiment seed."""

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed
        self._rng = random.Random(seed)

    @property
    def seed(self) -> int:
        return self._seed

    def reseed(self, seed: int) -> None:
        """Reset RNG state with a new or original seed."""
        self._seed = seed
        self._rng = random.Random(seed)

    def random(self) -> float:
        """Return random float in [0.0, 1.0)."""
        return self._rng.random()

    def uniform(self, a: float, b: float) -> float:
        """Return random float in [a, b]."""
        return self._rng.uniform(a, b)

    def randint(self, a: int, b: int) -> int:
        """Return random integer in [a, b], including both endpoints."""
        return self._rng.randint(a, b)

    def choice(self, seq: Sequence[T]) -> T:
        """Return a random element from a non-empty sequence."""
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        return self._rng.choice(seq)

    def sample(self, population: Sequence[T], k: int) -> list[T]:
        """Return a k length list of unique elements chosen from population."""
        return self._rng.sample(population, k)

    def shuffle(self, x: list[Any]) -> None:
        """Shuffle list in place deterministically."""
        self._rng.shuffle(x)

    def gauss(self, mu: float, sigma: float) -> float:
        """Return a random float from a Gaussian distribution."""
        return self._rng.gauss(mu, sigma)
