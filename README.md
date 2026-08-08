# Project Reading

Daily new-book discovery dashboard for history, culture, fiction, and notable authors.

## What It Does

- Fetches new-book feeds from configured sources.
- Filters books by preferred topics and excluded keywords.
- Deduplicates items that were already sent.
- Writes a static dashboard dataset to `docs/books.json`.
- Can run locally or from GitHub Actions.

## Data Sources

The default sources use RSSHub routes for several book-discovery platforms:

- https://rsshub.app/douban/book/latest
- https://rsshub.app/douban/bookstore
- https://rsshub.app/douban/book/rank/fiction
- https://rsshub.app/douban/book/rank/nonfiction
- https://rsshub.app/books/new

The config also keeps Yueke as a disabled candidate source. Yueke is a Douban-based new-book page that exposes RSS/JSON and updates every few hours, but its exact feed endpoint should be confirmed before enabling it:

- https://yueke.ababtools.com/

More sources can be added in `config/sources.json` without changing the code, as long as they provide RSS, Atom, or JSON items with title/link fields. Good next candidates are publisher new-release pages, bookstore new-release feeds, and literary media feeds.

## Requirements

- Python 3.10+
- A GitHub repository with Pages enabled through GitHub Actions

No third-party Python packages are required.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="src"
```

Or install the local command:

```powershell
pip install -e .
```

Optional: set the WeChat push credential when message delivery is enabled later:

```powershell
$env:SERVERCHAN_SENDKEY="SCT..."
```

Optional: use another RSSHub instance if `rsshub.app` is slow or unavailable from your runner:

```powershell
$env:RSSHUB_BASE_URL="https://your-rsshub.example.com"
```

## Run

Preview without sending:

```powershell
python -m new_book_alert --dry-run
```

Refresh dashboard data:

```powershell
python -m new_book_alert --skip-notify --dashboard docs/books.json
```

If installed with `pip install -e .`:

```powershell
new-book-alert --dry-run
```

Send the daily digest later, after setting `SERVERCHAN_SENDKEY`:

```powershell
python -m new_book_alert
```

Use a custom config or state file:

```powershell
python -m new_book_alert --config config/sources.json --state data/seen_books.json
```

## Dashboard

Open `docs/index.html` locally, or use GitHub Pages after the repository is pushed.

The dashboard reads `docs/books.json`, which is refreshed by the scheduled workflow every day at 08:30 China time.

## GitHub Actions

The workflow in `.github/workflows/daily-dashboard.yml` runs every day at 08:30 China time.

Optional repository secret for later WeChat delivery:

- `SERVERCHAN_SENDKEY`

Optional repository variable:

- `RSSHUB_BASE_URL`

The workflow commits the updated `docs/books.json` dashboard data and deploys the `docs` folder to GitHub Pages.

## Configuration

Edit `config/sources.json`:

- `sources`: RSS, Atom, or JSON feeds to scan.
- `include_keywords`: topics, authors, publishers, or categories to keep.
- `exclude_keywords`: noisy topics to drop.
- `max_items_per_digest`: cap the number of books in one message.

For JSON sources, set `items_path` when the item list is nested, and map fields with `fields`.

## Notes

- ServerChan Turbo free accounts currently have a small daily quota. Message delivery is kept optional while the dashboard is the primary interface.
- Douban-related feeds may change format or availability. Keep additional reputable sources in `config/sources.json` as fallbacks.
