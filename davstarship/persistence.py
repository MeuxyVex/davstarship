"""Persistence helpers for Davstarship player progress."""

from __future__ import annotations

import json
from pathlib import Path

SAVE_DIR = Path.home() / ".davstarship"
POINT_BALANCE_FILE = SAVE_DIR / "points.json"
SHOP_STATE_FILE = SAVE_DIR / "shop.json"
DEFAULT_PILOT_ID = "earth racer"
DEFAULT_OWNED_PILOTS = {DEFAULT_PILOT_ID}


def load_point_balance(save_file: Path = POINT_BALANCE_FILE) -> int:
    """Return the saved point balance, or 0 when no valid save exists."""
    try:
        data = json.loads(save_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return 0

    if not isinstance(data, dict):
        return 0

    points = data.get("points")
    if not isinstance(points, int) or points < 0:
        return 0
    return points


def save_point_balance(points: int, save_file: Path = POINT_BALANCE_FILE) -> None:
    """Persist the point balance to a dedicated save file."""
    if points < 0:
        raise ValueError("Point balance cannot be negative")

    save_file.parent.mkdir(parents=True, exist_ok=True)
    save_file.write_text(json.dumps({"points": points}), encoding="utf-8")


def load_shop_state(
    save_file: Path = SHOP_STATE_FILE,
) -> tuple[set[str], str]:
    """Return owned pilots and equipped pilot from the shop save file."""
    try:
        data = json.loads(save_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set(DEFAULT_OWNED_PILOTS), DEFAULT_PILOT_ID

    if not isinstance(data, dict):
        return set(DEFAULT_OWNED_PILOTS), DEFAULT_PILOT_ID

    owned_pilots_data = data.get("owned_pilots")
    equipped_pilot = data.get("equipped_pilot")
    if not isinstance(owned_pilots_data, list) or not all(
        isinstance(pilot_id, str) for pilot_id in owned_pilots_data
    ):
        return set(DEFAULT_OWNED_PILOTS), DEFAULT_PILOT_ID

    owned_pilots = set(owned_pilots_data)
    owned_pilots.add(DEFAULT_PILOT_ID)
    if not isinstance(equipped_pilot, str) or equipped_pilot not in owned_pilots:
        equipped_pilot = DEFAULT_PILOT_ID

    return owned_pilots, equipped_pilot


def save_shop_state(
    owned_pilots: set[str],
    equipped_pilot: str,
    save_file: Path = SHOP_STATE_FILE,
) -> None:
    """Persist owned pilots and the currently equipped pilot."""
    safe_owned_pilots = set(owned_pilots)
    safe_owned_pilots.add(DEFAULT_PILOT_ID)
    if equipped_pilot not in safe_owned_pilots:
        raise ValueError("Equipped pilot must be owned")
    save_file.parent.mkdir(parents=True, exist_ok=True)
    save_file.write_text(
        json.dumps(
            {
                "owned_pilots": sorted(safe_owned_pilots),
                "equipped_pilot": equipped_pilot,
            }
        ),
        encoding="utf-8",
    )
