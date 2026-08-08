from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
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
    payload = {
        "generated_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "timezone": "Asia/Shanghai",
        "fetched_count": fetched_count,
        "matched_count": matched_count,
        "source_errors": source_errors,
        "books": [asdict(book) for book in books],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
