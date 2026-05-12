from random import Random

import pytest

from davstarship.game_objects import (
    ASTEROID_VARIANT_SIZES,
    COIN_SIZE,
    RED_PILL_SIZE,
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
    assert asteroid.variant in ASTEROID_VARIANT_SIZES
    assert asteroid.width == ASTEROID_VARIANT_SIZES[asteroid.variant]
    assert asteroid.y == -asteroid.height
    assert 8 <= asteroid.x <= SCREEN_WIDTH - asteroid.width - 8


def test_random_falling_object_can_force_asteroid_variant():
    asteroid = random_falling_object("asteroid", Random(4), variant="big")
    assert asteroid.variant == "big"
    assert asteroid.width == ASTEROID_VARIANT_SIZES["big"]


def test_random_falling_object_can_create_red_pill():
    pill = random_falling_object("red_pill", Random(4))
    assert pill.kind == "red_pill"
    assert pill.variant is None
    assert pill.width == RED_PILL_SIZE
    assert pill.height == RED_PILL_SIZE
    assert pill.y == -pill.height
    assert 8 <= pill.x <= SCREEN_WIDTH - pill.width - 8


def test_falling_object_sizes_are_coherent():
    assert COIN_SIZE > 0
    assert RED_PILL_SIZE > 0
    assert abs(RED_PILL_SIZE - COIN_SIZE) <= 8
    assert min(ASTEROID_VARIANT_SIZES.values()) > RED_PILL_SIZE


def test_random_falling_object_rejects_unknown_kind():
    with pytest.raises(ValueError):
        random_falling_object("bonus", Random(4))


def test_random_falling_object_rejects_unknown_asteroid_variant():
    with pytest.raises(ValueError):
        random_falling_object("asteroid", Random(4), variant="giant")
