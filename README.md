# Kiwi Rates

Automated daily scraping of New Zealand bank home loan rates with minimal maintenance.

## Features

- **Automated daily scraping** via GitHub Actions
- **Stateful updates** - only stores rate changes, not duplicates
- **Rate change tracking** - visualizes how rates changed since previous scrape with color-coded indicators and highlights recent changes (last 14 days) with yellow background
- **New product badges** - identifies loan products introduced within last 30 days
- **Mobile responsive** - card-based layout optimized for mobile screens
- **Zero maintenance** - auto-extracts API keys from bank websites
- **Free hosting** - GitHub Pages serves static HTML visualization
- **Extensible** - designed to easily add more banks
- **Comprehensive tests** - 50 unit tests with TDD approach

## Current Banks

- BNZ (Bank of New Zealand)

## Bank Module Architecture

Each bank is implemented as a separate module (`src/bnz/`, `src/anz/`, etc.) containing:

- **`extractor.py`** - Extract API keys/tokens from bank's website
- **`parser.py`** - Parse bank-specific data format (XML, JSON, HTML)
- **`scraper.py`** - Orchestrate the scraping process (fetch → parse → store)
- **`__init__.py`** - Export the main scraper function

**Shared utilities:**
- `storage.py` - JSON file operations (works with all banks)
- `html_generator.py` - Generates visualization from all bank data files

This modular design makes adding new banks straightforward and keeps bank-specific code isolated.

## Architecture

- **Language**: Python 3.14
- **Package Manager**: uv
- **Dependencies**: requests (HTTP), pytest (testing), stdlib (everything else)
- **Storage**: JSON files (one per bank)
- **Hosting**: GitHub Pages
- **CI/CD**: GitHub Actions

## Project Structure

```
/
├── .github/workflows/scrape.yml  # Daily cron job
├── src/
│   ├── bnz/                      # BNZ-specific scraper module
│   │   ├── __init__.py          # Exports scrape_bnz_rates
│   │   ├── extractor.py         # Extract API key from HTML
│   │   ├── parser.py            # Parse BNZ XML feed
│   │   └── scraper.py           # BNZ scraping orchestration
│   ├── scraper.py               # Main entry point
│   ├── storage.py               # JSON file operations (bank-agnostic)
│   └── html_generator.py        # Generate static HTML (bank-agnostic)
├── data/
│   └── bnz_rates.json           # BNZ historical rate data
├── docs/
│   └── index.html               # Auto-generated visualization
├── tests/
│   ├── fixtures/                # Static test data
│   ├── test_api_key_extractor.py
│   ├── test_bnz_parser.py
│   ├── test_storage.py
│   └── test_html_generator.py
├── pyproject.toml               # Project config & dependencies
├── PROJECT_SPEC.md              # Detailed specification
└── README.md                    # This file
```

## Data Model

Each bank has a separate JSON file (`data/{bank}_rates.json`):

```json
{
  "bank_last_updated": "2025-12-18T00:00:00+13:00",
  "rates": [
    {
      "scraped_at": "2025-12-15T12:00:00+13:00",
      "product_name": "Standard",
      "term": "1 year",
      "rate_percentage": 4.49
    }
  ]
}
```

### Stateful Updates

- `bank_last_updated` - when bank claims rates were updated
- `rates` - only appends new entries when values actually change
- Scraper health monitored via GitHub Actions failure notifications

## Setup

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd kiwi-rates
```

2. Install dependencies:
```bash
uv sync
```

3. Run tests:
```bash
uv run pytest -v
```

4. Run scraper manually:
```bash
uv run python -m src.scraper
```

5. Generate HTML:
```bash
uv run python -m src.html_generator
```

6. View the generated HTML:
```bash
open docs/index.html
```

### Git Pre-Push Hook (Optional)

To automatically run tests before every push, set up the pre-push hook:

```bash
# Copy the hook
cp .git/hooks/pre-push.sample .git/hooks/pre-push

# Or create it manually:
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
echo "Running tests before push..."
uv run pytest
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Push aborted."
    exit 1
fi
echo "✅ All tests passed! Proceeding with push."
exit 0
EOF

# Make it executable
chmod +x .git/hooks/pre-push
```

**Note:** Git hooks are not tracked in the repository. Each developer needs to set this up locally.

## GitHub Setup

### Enable GitHub Pages

1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `master`, Folder: `/docs`
4. Save

Your rates will be available at: `https://<username>.github.io/<repo-name>/`

**Note:** GitHub Pages may need to be manually enabled in repository settings if not already active.

### Manual Trigger

You can manually trigger the scraper from the Actions tab:

1. Go to Actions → "Scrape Bank Rates"
2. Click "Run workflow"

## How It Works

### BNZ Scraping Process

1. **Fetch HTML page** (`src/bnz/scraper.py`) - Get the BNZ home loans page
2. **Extract API key** (`src/bnz/extractor.py`) - Parse `window.__bootstrap.apiKey` from JavaScript
3. **Fetch rates XML** (`src/bnz/scraper.py`) - Call BNZ API with extracted key
4. **Parse XML** (`src/bnz/parser.py`) - Extract product names, terms, and rates
5. **Compare** (`src/storage.py`) - Check if rates changed vs last scrape
6. **Update** (`src/storage.py`) - Save to JSON if changed
7. **Generate HTML** (`src/html_generator.py`) - Create visualization with rate change indicators
   - Compares each product/term to previous scrape
   - Displays: `5.55% (+0.26)` for increases (red), `4.49% (-0.20)` for decreases (green), `4.49% (0.00)` for no change (gray)
   - Highlights rows with changes in last 14 days (yellow background) for quick identification of recent market movements
   - Shows blue "NEW" badge next to product names for products first appearing within last 30 days
   - Top header shows most recent rate change date across all banks
   - Each bank table includes "Page generated" and "Data last scraped" timestamps below the table
8. **Commit & Push** (GitHub Actions) - Update repository

### Retry Logic

- Failed requests retry 3 times with exponential backoff
- Prevents transient failures from breaking the scraper

### Why It's Low Maintenance

- **No API key storage** - Always extracts fresh key from website
- **No browser automation** - Simple HTTP requests (fast, reliable)
- **Stateful updates** - Only stores changes (clean data, less git noise)
- **Comprehensive tests** - 50 tests ensure reliability

## Adding More Banks

To add another bank (e.g., ANZ), follow the bank module pattern:

### 1. Create Bank Module

Create `src/anz/` directory with these files:

**`src/anz/__init__.py`** - Export main function:
```python
from src.anz.scraper import scrape_anz_rates
__all__ = ["scrape_anz_rates"]
```

**`src/anz/extractor.py`** - Extract API key/tokens from ANZ HTML

**`src/anz/parser.py`** - Parse ANZ-specific data format (XML/JSON/HTML)

**`src/anz/scraper.py`** - Orchestrate ANZ scraping (fetch → parse → store)

### 2. Update Main Scraper

Add ANZ call in `src/scraper.py`:
```python
from src.bnz import scrape_bnz_rates
from src.anz import scrape_anz_rates

# Call both scrapers
scrape_bnz_rates(bnz_file)
scrape_anz_rates(anz_file)
```

### 3. Update GitHub Actions

Add ANZ to `.github/workflows/scrape.yml` (it will auto-detect new bank files)

### 4. Create Data File

Create seed file `data/anz_rates.json` with empty structure

### 5. Add Tests

Create `tests/test_anz_*.py` files following BNZ test patterns

**Shared utilities** (`storage.py`, `html_generator.py`) work with all banks automatically.

See `PROJECT_SPEC.md` for detailed design decisions.

## Testing

All tests use static fixtures (no live API calls):

```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest tests/test_bnz_parser.py -v

# Run with coverage
uv run pytest --cov=src
```

## Schedule

- **Frequency**: Daily at 11 PM NZ time (10:00 UTC)
- **Duration**: ~5-10 seconds per run
- **Cost**: $0 (within GitHub Actions free tier)

## Troubleshooting

### How to verify scraper health

The scraper is monitored via GitHub Actions:
- **Workflow succeeds**: Scraper ran successfully (may or may not have committed changes)
- **Workflow fails**: You'll receive email notification with error details
- Check "Page generated:" timestamp in HTML to confirm recent successful run
- All errors are loud failures - no silent data corruption

Common failure scenarios:
- BNZ website structure changed (API key extraction fails)
- BNZ API returned empty data (no rates found)
- Network issues (after 5 retries with exponential backoff)
- Malformed data in JSON files

### Scraper fails with 403 error

The API may be blocking requests. Check if headers need updating in `src/bnz/scraper.py`.

### Rates not updating

Check:
1. GitHub Actions logs for errors (you'll receive email notifications on workflow failures)
2. "Page generated:" timestamp in the HTML visualization
3. Bank's website is accessible

### Tests failing

```bash
# Ensure dependencies are installed
uv sync

# Run tests with verbose output
uv run pytest -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests (TDD approach)
4. Implement feature
5. Ensure all tests pass
6. Submit pull request

## License

MIT

## Acknowledgments

- Built with Test-Driven Development
- Follows minimal maintenance principles
- Designed for extensibility
