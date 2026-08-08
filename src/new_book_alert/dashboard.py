from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .fetchers import BookItem


def write_dashboard_data(
    path: Path,
    books: list[BookItem],
    source_errors: list[str],
    fetched_count: int,
    matched_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    timezone = ZoneInfo("Asia/Shanghai")
    now = datetime.now(timezone)
    existing = _load_existing_books(path)
    records: dict[str, dict] = {}

    for book in books:
        record = asdict(book)
        previous = existing.get(book.id, {})
        record["discovered_at"] = previous.get("discovered_at") or now.isoformat(timespec="seconds")
        records[book.id] = record

    cutoff = now.date() - timedelta(days=6)
    for book_id, record in existing.items():
        if book_id in records:
            continue
        discovered_at = _parse_datetime(record.get("discovered_at"), timezone)
        if discovered_at and cutoff <= discovered_at.date() < now.date():
            records[book_id] = record

    retained_books = sorted(
        records.values(),
        key=lambda item: (item.get("discovered_at", ""), item.get("published", ""), item.get("title", "")),
        reverse=True,
    )
    payload = {
        "generated_at": now.isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "fetched_count": fetched_count,
        "matched_count": matched_count,
        "source_errors": source_errors,
        "books": retained_books,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_existing_books(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    fallback_discovered_at = payload.get("generated_at", "")
    existing: dict[str, dict] = {}
    for record in payload.get("books", []):
        if not isinstance(record, dict) or not record.get("id"):
            continue
        normalized = dict(record)
        normalized["discovered_at"] = normalized.get("discovered_at") or fallback_discovered_at
        existing[normalized["id"]] = normalized
    return existing


def _parse_datetime(value: str | None, timezone: ZoneInfo) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone)
