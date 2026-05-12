import pytest

from davstarship.persistence import (
    DEFAULT_PILOT_ID,
    load_point_balance,
    load_shop_state,
    save_point_balance,
    save_shop_state,
)


def test_point_balance_defaults_to_zero_when_save_is_missing(tmp_path):
    assert load_point_balance(tmp_path / "points.json") == 0


def test_point_balance_is_saved_and_loaded_from_specific_file(tmp_path):
    save_file = tmp_path / "profile" / "points.json"

    save_point_balance(12, save_file)

    assert load_point_balance(save_file) == 12
    assert save_file.read_text(encoding="utf-8") == '{"points": 12}'


def test_point_balance_rejects_negative_values(tmp_path):
    with pytest.raises(ValueError):
        save_point_balance(-1, tmp_path / "points.json")


def test_point_balance_ignores_invalid_save_data(tmp_path):
    save_file = tmp_path / "points.json"
    save_file.write_text('{"points": "many"}', encoding="utf-8")

    assert load_point_balance(save_file) == 0


def test_point_balance_ignores_non_object_json(tmp_path):
    save_file = tmp_path / "points.json"
    save_file.write_text("[]", encoding="utf-8")

    assert load_point_balance(save_file) == 0


def test_shop_state_defaults_to_earth_racer_when_save_is_missing(tmp_path):
    owned_pilots, equipped_pilot = load_shop_state(tmp_path / "shop.json")

    assert owned_pilots == {DEFAULT_PILOT_ID}
    assert equipped_pilot == DEFAULT_PILOT_ID


def test_shop_state_is_saved_and_loaded_from_specific_file(tmp_path):
    save_file = tmp_path / "profile" / "shop.json"

    save_shop_state({DEFAULT_PILOT_ID, "moon racer"}, "moon racer", save_file)

    assert load_shop_state(save_file) == (
        {DEFAULT_PILOT_ID, "moon racer"},
        "moon racer",
    )


def test_shop_state_always_keeps_default_pilot_owned(tmp_path):
    save_file = tmp_path / "shop.json"

    save_shop_state(set(), DEFAULT_PILOT_ID, save_file)

    assert load_shop_state(save_file) == ({DEFAULT_PILOT_ID}, DEFAULT_PILOT_ID)


def test_shop_state_falls_back_when_equipped_pilot_is_not_owned(tmp_path):
    save_file = tmp_path / "shop.json"
    save_file.write_text(
        '{"owned_pilots": ["moon racer"], "equipped_pilot": "sun racer"}',
        encoding="utf-8",
    )

    assert load_shop_state(save_file) == (
        {DEFAULT_PILOT_ID, "moon racer"},
        DEFAULT_PILOT_ID,
    )


def test_shop_state_defaults_to_earth_racer_for_non_object_json(tmp_path):
    save_file = tmp_path / "shop.json"
    save_file.write_text("[]", encoding="utf-8")

    assert load_shop_state(save_file) == ({DEFAULT_PILOT_ID}, DEFAULT_PILOT_ID)


def test_shop_state_rejects_unowned_equipped_pilot(tmp_path):
    with pytest.raises(ValueError):
        save_shop_state({DEFAULT_PILOT_ID}, "moon racer", tmp_path / "shop.json")
