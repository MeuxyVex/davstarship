from random import Random

import pytest

from davstarship.game_objects import (
    SCREEN_WIDTH,
    asteroid_spawn_interval,
    coin_spawn_interval,
    random_falling_object,
    rects_overlap,
)


def test_rects_overlap_detects_collision_and_separation():
    assert rects_overlap((0, 0, 20, 20), (10, 10, 20, 20))
    assert not rects_overlap((0, 0, 20, 20), (30, 30, 20, 20))


def test_asteroid_spawn_interval_gets_faster_but_is_clamped():
    assert asteroid_spawn_interval(0) == 1.15
    assert asteroid_spawn_interval(24) < asteroid_spawn_interval(0)
    assert asteroid_spawn_interval(10_000) == 0.35


def test_coin_spawn_interval_gets_faster_but_is_clamped():
    assert coin_spawn_interval(0) == 1.9
    assert coin_spawn_interval(50) < coin_spawn_interval(0)
    assert coin_spawn_interval(10_000) == 0.85


def test_random_falling_object_starts_above_screen_and_within_width():
    asteroid = random_falling_object("asteroid", Random(4))
    assert asteroid.kind == "asteroid"
    assert asteroid.y == -asteroid.height
    assert 8 <= asteroid.x <= SCREEN_WIDTH - asteroid.width - 8


def test_random_falling_object_rejects_unknown_kind():
    with pytest.raises(ValueError):
        random_falling_object("bonus", Random(4))
