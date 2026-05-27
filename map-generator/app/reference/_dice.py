"""Boundary-isolated d20 roller."""
from __future__ import annotations
import random

_DIE_MIN = 1
_DIE_MAX = 20


def roll_d20(rng: random.Random | None = None) -> int:
    source = rng or random
    return source.randint(_DIE_MIN, _DIE_MAX)
