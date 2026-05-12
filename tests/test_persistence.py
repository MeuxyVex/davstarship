import pytest

from davstarship.persistence import load_point_balance, save_point_balance


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
