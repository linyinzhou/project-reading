from __future__ import annotations

import json
from pathlib import Path


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {str(item) for item in data}
    if isinstance(data, dict):
        return {str(item) for item in data.get("seen_ids", [])}
    return set()


def save_seen(path: Path, seen_ids: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"seen_ids": sorted(seen_ids)}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
