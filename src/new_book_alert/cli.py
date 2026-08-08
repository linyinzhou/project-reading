from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a daily new-book digest to WeChat.")
    parser.add_argument("--config", default="config/sources.json", help="Path to source configuration.")
    parser.add_argument("--state", default="data/seen_books.json", help="Path to dedupe state.")
    parser.add_argument("--dry-run", action="store_true", help="Print digest without sending it.")
    parser.add_argument("--skip-notify", action="store_true", help="Do not send the WeChat notification.")
    parser.add_argument("--dashboard", help="Write dashboard JSON data to this path.")
    args = parser.parse_args()

    result = run(
        config_path=Path(args.config),
        state_path=Path(args.state),
        dry_run=args.dry_run,
        skip_notify=args.skip_notify,
        dashboard_path=Path(args.dashboard) if args.dashboard else None,
    )

    print(result.message)
    if result.digest:
        print()
        print(result.digest)

    return 0 if result.ok else 1
