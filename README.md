# Project Reading

Daily new-book discovery dashboard for history, culture, fiction, and notable authors.

## What It Does

- Fetches new-book listings from configured sources.
- Filters books by preferred topics and excluded keywords.
- Deduplicates items that were already sent.
- Keeps a rolling seven-day discovery history.
- Writes a static dashboard dataset to `docs/books.json`.
- Can run locally or from GitHub Actions.

## Data Sources

The default sources read the literature, fiction, history and culture, social nonfiction, and art and design categories from Douban's New Book Express pages:

- https://book.douban.com/latest

The config keeps the previous RSSHub routes and Yueke endpoints as disabled fallback candidates. They can be re-enabled when a stable instance is available:

- https://yueke.ababtools.com/

More sources can be added in `config/sources.json` without changing the code when they provide RSS, Atom, or JSON items with title/link fields. The `douban_latest` source type handles Douban New Book Express category pages.

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

The dashboard reads `docs/books.json`, which is refreshed by the scheduled workflow every day at 08:30 China time. Books are grouped by the day this project first discovered them: today and the preceding six days.

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
- Douban may change its page format or availability. Keep additional reputable sources in `config/sources.json` as fallbacks.
