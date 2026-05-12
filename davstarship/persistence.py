"""Persistence helpers for Davstarship player progress."""

from __future__ import annotations

import json
from pathlib import Path

SAVE_DIR = Path.home() / ".davstarship"
POINT_BALANCE_FILE = SAVE_DIR / "points.json"


def load_point_balance(save_file: Path = POINT_BALANCE_FILE) -> int:
    """Return the saved point balance, or 0 when no valid save exists."""
    try:
        data = json.loads(save_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
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
