from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Source:
    name: str
    type: str
    url: str
    enabled: bool = True
    items_path: str | None = None
    fields: dict[str, str] | None = None


@dataclass(frozen=True)
class AppConfig:
    sources: list[Source]
    include_keywords: list[str]
    exclude_keywords: list[str]
    max_items_per_digest: int
    request_timeout_seconds: int


def load_config(path: Path) -> AppConfig:
    data = json.loads(path.read_text(encoding="utf-8"))
    sources = [Source(**item) for item in data.get("sources", []) if item.get("enabled", True)]

    return AppConfig(
        sources=sources,
        include_keywords=data.get("include_keywords", []),
        exclude_keywords=data.get("exclude_keywords", []),
        max_items_per_digest=int(data.get("max_items_per_digest", 12)),
        request_timeout_seconds=int(data.get("request_timeout_seconds", 20)),
    )


def get_nested(data: Any, path: str | None) -> Any:
    if not path:
        return data

    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current
