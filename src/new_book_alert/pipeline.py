from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import load_config
from .dashboard import write_dashboard_data
from .fetchers import BookItem, fetch_source
from .filters import filter_books
from .notifier import NotificationError, send_serverchan
from .storage import load_seen, save_seen


@dataclass(frozen=True)
class RunResult:
    ok: bool
    message: str
    digest: str


def run(
    config_path: Path,
    state_path: Path,
    dry_run: bool,
    skip_notify: bool = False,
    dashboard_path: Path | None = None,
) -> RunResult:
    config = load_config(config_path)
    fetched: list[BookItem] = []
    errors: list[str] = []

    for source in config.sources:
        try:
            fetched.extend(fetch_source(source, config.request_timeout_seconds))
        except Exception as exc:
            errors.append(f"{source.name}: {exc}")

    matched = filter_books(fetched, config.include_keywords, config.exclude_keywords)
    dashboard_books = matched[: config.max_items_per_digest]
    if dashboard_path:
        write_dashboard_data(
            dashboard_path,
            dashboard_books,
            errors,
            fetched_count=len(fetched),
            matched_count=len(matched),
        )

    seen = load_seen(state_path)
    new_books = [book for book in matched if book.id not in seen]
    selected = new_books[: config.max_items_per_digest]

    if skip_notify:
        digest = format_digest(dashboard_books, errors) if dashboard_books else _format_errors(errors)
        message = f"dashboard updated: fetched={len(fetched)}, matched={len(matched)}"
        if errors:
            message += f", source_errors={len(errors)}"
        return RunResult(ok=True, message=message, digest=digest)

    if not selected:
        message = f"No new matched books. fetched={len(fetched)}, matched={len(matched)}"
        if errors:
            message += f", source_errors={len(errors)}"
        return RunResult(ok=not errors, message=message, digest=_format_errors(errors))

    digest = format_digest(selected, errors)

    if not dry_run:
        try:
            send_serverchan("今日新书提醒", digest)
        except NotificationError as exc:
            return RunResult(ok=False, message=str(exc), digest=digest)

    seen.update(book.id for book in selected)
    save_seen(state_path, seen)

    mode = "dry-run" if dry_run else "sent"
    return RunResult(
        ok=True,
        message=f"{mode}: {len(selected)} new books, fetched={len(fetched)}, matched={len(matched)}",
        digest=digest,
    )


def format_digest(books: list[BookItem], errors: list[str] | None = None) -> str:
    today = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    lines = [f"## 今日新书提醒（{today}）", ""]

    for index, book in enumerate(books, start=1):
        title = book.title or "Untitled"
        link = book.link or ""
        if link:
            lines.append(f"{index}. [{title}]({link})")
        else:
            lines.append(f"{index}. {title}")

        details = []
        if book.author:
            details.append(f"作者：{book.author}")
        if book.published:
            details.append(f"时间：{book.published}")
        details.append(f"来源：{book.source}")
        lines.append("   " + "；".join(details))

        if book.summary:
            summary = book.summary[:180] + ("..." if len(book.summary) > 180 else "")
            lines.append(f"   {summary}")
        lines.append("")

    if errors:
        lines.extend(["### 数据源提醒", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")

    return "\n".join(lines).strip()


def _format_errors(errors: list[str]) -> str:
    if not errors:
        return ""
    return "\n".join(["Source errors:", *[f"- {error}" for error in errors]])
