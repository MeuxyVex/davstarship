import pytest

pytest.importorskip("pygame")

from davstarship.main import DavstarshipGame


PILOTS = [
    {"id": "earth racer", "name": "earth racer", "price": 0, "speed": 360.0},
    {"id": "moon racer", "name": "moon racer", "price": 50, "speed": 460.0},
    {"id": "sun racer", "name": "sun racer", "price": 120, "speed": 560.0},
]


def make_game() -> DavstarshipGame:
    game = DavstarshipGame.__new__(DavstarshipGame)
    game.pilots = [dict(pilot) for pilot in PILOTS]
    game.owned_pilots = {"earth racer"}
    game.equipped_pilot_id = "earth racer"
    game.selected_pilot_index = 0
    game.point_balance = 0
    game.shop_message = ""
    return game


def test_current_player_speed_uses_equipped_pilot():
    game = make_game()
    game.owned_pilots.add("sun racer")
    game.equipped_pilot_id = "sun racer"

    assert game.current_player_speed() == 560.0


def test_shop_navigation_wraps_between_pilots():
    game = make_game()

    game.select_previous_pilot()
    assert game.current_pilot()["id"] == "sun racer"

    game.select_next_pilot()
    assert game.current_pilot()["id"] == "earth racer"


def test_buy_or_equip_selected_pilot_buys_saves_and_equips(monkeypatch):
    game = make_game()
    game.point_balance = 50
    game.selected_pilot_index = 1
    saved_points = []
    saved_shop_states = []

    monkeypatch.setattr("davstarship.main.save_point_balance", saved_points.append)
    monkeypatch.setattr(
        "davstarship.main.save_shop_state",
        lambda owned, equipped: saved_shop_states.append((set(owned), equipped)),
    )

    game.buy_or_equip_selected_pilot()

    assert game.point_balance == 0
    assert game.owned_pilots == {"earth racer", "moon racer"}
    assert game.equipped_pilot_id == "moon racer"
    assert saved_points == [0]
    assert saved_shop_states == [({"earth racer", "moon racer"}, "moon racer")]


def test_buy_or_equip_selected_pilot_does_not_buy_without_enough_points(monkeypatch):
    game = make_game()
    game.point_balance = 20
    game.selected_pilot_index = 1
    saved_points = []
    saved_shop_states = []

    monkeypatch.setattr("davstarship.main.save_point_balance", saved_points.append)
    monkeypatch.setattr(
        "davstarship.main.save_shop_state",
        lambda owned, equipped: saved_shop_states.append((set(owned), equipped)),
    )

    game.buy_or_equip_selected_pilot()

    assert game.point_balance == 20
    assert game.owned_pilots == {"earth racer"}
    assert game.equipped_pilot_id == "earth racer"
    assert game.shop_message == "Il manque 30 points."
    assert saved_points == []
    assert saved_shop_states == []
