from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from new_book_alert.dashboard import write_dashboard_data
from new_book_alert.fetchers import BookItem


class DashboardHistoryTests(unittest.TestCase):
    def test_preserves_recent_discoveries_and_drops_expired_books(self) -> None:
        timezone = ZoneInfo("Asia/Shanghai")
        now = datetime.now(timezone)
        current_discovered_at = (now - timedelta(days=2)).isoformat(timespec="seconds")
        recent_discovered_at = (now - timedelta(days=4)).isoformat(timespec="seconds")
        expired_discovered_at = (now - timedelta(days=8)).isoformat(timespec="seconds")
        omitted_today = now.isoformat(timespec="seconds")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "books.json"
            path.write_text(
                json.dumps(
                    {
                        "generated_at": expired_discovered_at,
                        "books": [
                            {"id": "current", "title": "Current", "discovered_at": current_discovered_at},
                            {"id": "recent", "title": "Recent", "discovered_at": recent_discovered_at},
                            {"id": "expired", "title": "Expired", "discovered_at": expired_discovered_at},
                            {"id": "omitted", "title": "Omitted", "discovered_at": omitted_today},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            write_dashboard_data(
                path,
                [BookItem(id="current", title="Current", link="", source="Test")],
                [],
                fetched_count=1,
                matched_count=1,
            )

            payload = json.loads(path.read_text(encoding="utf-8"))
            records = {book["id"]: book for book in payload["books"]}
            self.assertEqual(set(records), {"current", "recent"})
            self.assertEqual(records["current"]["discovered_at"], current_discovered_at)


if __name__ == "__main__":
    unittest.main()
