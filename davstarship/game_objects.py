"""Core game objects and difficulty rules for Davstarship.

This module intentionally has no pygame dependency so it can be unit-tested in
headless environments. The pygame layer imports these constants and helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_WIDTH = 54
PLAYER_HEIGHT = 46
PLAYER_Y_MARGIN = 30
PLAYER_SPEED = 420.0
FALL_SPEED = 220.0
ASTEROID_VARIANT_SIZES = {"little": 34, "mid": 48, "big": 66}
ASTEROID_SIZE = ASTEROID_VARIANT_SIZES["mid"]
COIN_SIZE = 28


@dataclass(slots=True)
class FallingObject:
    """Object that falls from the top of the screen."""

    kind: str
    x: float
    y: float
    width: int
    height: int
    speed: float = FALL_SPEED
    variant: str | None = None

    @property
    def rect(self) -> tuple[float, float, int, int]:
        """Return a simple rectangle tuple for collision checks."""
        return (self.x, self.y, self.width, self.height)

    def update(self, delta_seconds: float) -> None:
        """Move the object down according to the fixed fall speed."""
        self.y += self.speed * delta_seconds

    def is_off_screen(self, screen_height: int = SCREEN_HEIGHT) -> bool:
        """Return whether the object is fully below the play area."""
        return self.y > screen_height


def rects_overlap(
    first: tuple[float, float, int, int], second: tuple[float, float, int, int]
) -> bool:
    """Return True when two axis-aligned rectangles overlap."""
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def asteroid_spawn_interval(elapsed_seconds: float) -> float:
    """Return the current asteroid spawn interval.

    Asteroids keep the same fall speed for the whole game, but they appear more
    often as survival time increases. The interval is clamped so the game stays
    playable and deterministic.
    """
    return max(0.35, 1.15 - (elapsed_seconds // 12) * 0.12)


def coin_spawn_interval(elapsed_seconds: float) -> float:
    """Return the current coin spawn interval."""
    return max(0.85, 1.9 - (elapsed_seconds // 25) * 0.08)


def random_falling_object(
    kind: str, rng: Random, variant: str | None = None
) -> FallingObject:
    """Create a random asteroid or coin at the top of the screen."""
    if kind == "asteroid":
        asteroid_variant = variant or rng.choice(tuple(ASTEROID_VARIANT_SIZES))
        if asteroid_variant not in ASTEROID_VARIANT_SIZES:
            raise ValueError(f"Unsupported asteroid variant: {asteroid_variant}")
        size = ASTEROID_VARIANT_SIZES[asteroid_variant]
        object_variant = asteroid_variant
    elif kind == "coin":
        size = COIN_SIZE
        object_variant = None
    else:
        raise ValueError(f"Unsupported falling object kind: {kind}")

    return FallingObject(
        kind=kind,
        x=rng.randint(8, SCREEN_WIDTH - size - 8),
        y=-size,
        width=size,
        height=size,
        variant=object_variant,
    )
