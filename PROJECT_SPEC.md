# Kiwi Rates - Project Specification

## Project Goal
Automated daily scraping of NZ bank home loan rates with minimal future maintenance. Solution designed for multiple banks.

## Requirements
- Daily automated scraping
- Long-term solution with minimal maintenance
- Low cost (preferably free)
- Store historical data
- Simple HTML visualization
- Focus on BNZ initially, extensible to other banks

## Architecture

### Deployment: GitHub Actions + GitHub Pages
- **GitHub Actions**: Daily cron job for scraping (free tier: 2000 mins/month)
- **GitHub Pages**: Free static HTML hosting with HTTPS
- **Git Repository**: Version control doubles as backup for historical data

### Data Storage: JSON Files (One per Bank)
- Separate JSON file per bank: `data/bnz_rates.json`, `data/anz_rates.json`, etc.
- Append-only structure for historical tracking
- Human-readable, easy to query with Python/jq
- Bank identified by filename (no `bank_name` field needed)

### Hosting: GitHub Pages
- Static HTML served from `docs/` directory
- Simple table view of rates
- No alerting/monitoring for now

## Technical Approach

### Scraping Method: API-based (No Browser Automation)
1. **Fetch HTML page** to extract current API key
   - URL: `https://www.bnz.co.nz/personal-banking/home-loans/compare-bnz-home-loan-rates`
   - Extract `apiKey` from `window.__bootstrap` JavaScript object
   - Regex pattern: `window\.__bootstrap\s*=\s*\{[^}]*apiKey:\s*'([^']+)'`

2. **Call BNZ API** with extracted key
   - Endpoint: `https://api.bnz.co.nz/v1/ratesfeed/home/xml`
   - Format: XML response
   - Headers required:
     - `apikey`: (extracted from step 1)
     - `Accept`: `application/xml, text/xml`
     - `Referer`: `https://www.bnz.co.nz/`
     - `Origin`: `https://www.bnz.co.nz`

3. **Parse XML** and extract rate data

4. **Store in JSON** file

5. **Generate HTML** table

6. **Commit and push** to repository

### Why This Approach?
- **No API key storage**: Always fetches current key from HTML (zero maintenance if key rotates)
- **No browser automation**: Lightweight, fast, reliable (uses `requests` library only)
- **Simple**: 2 HTTP requests + XML parsing + JSON file operations
- **Resilient**: API keys are public (embedded in frontend), so extraction always works

## Data Model

### JSON Structure (per bank file, e.g., `data/bnz_rates.json`)
```json
{
  "bank_last_updated": "2025-12-18T00:00:00+13:00",
  "rates": [
    {
      "scraped_at": "2025-12-15T12:00:00+13:00",
      "product_name": "Standard",
      "term": "1 year",
      "rate_percentage": 4.49
    },
    {
      "scraped_at": "2025-12-15T12:00:00+13:00",
      "product_name": "TotalMoney",
      "term": "Variable",
      "rate_percentage": 5.94
    }
  ]
}
```

### Top-Level Fields
- `bank_last_updated`: ISO timestamp with NZ timezone - when bank claims rates were last updated (null if bank doesn't provide this data)

### Rate Entry Fields
- `scraped_at`: ISO timestamp with NZ timezone - when this rate value was first scraped
- `product_name`: Product/loan type (e.g., "Standard", "TotalMoney", "BNZ Advantage")
- `term`: Loan term (e.g., "Variable", "6 months", "1 year", "2 years")
- `rate_percentage`: Interest rate as decimal

### Storage Strategy
- **Stateful updates**: Only append new entries to `rates` array when values actually change (implemented via `filter_changed_rates()` function)
- **Comparison logic**: For each product/term combination, compare new rate against last entry; only store if different
- **Bank name**: Identified by filename (`bnz_rates.json`, `anz_rates.json`, etc.), not stored in data
- **Timezone**: All timestamps use NZ timezone (Pacific/Auckland, UTC+12/+13 depending on DST)

### BNZ XML Feed Structure
BNZ API returns XML in this format:
```xml
<rss version="2.0">
  <standard type="HL">
    <lastupdated>Thursday, 18 December 2025</lastupdated>
    <rate id="HL-HS01-1YEAR">
      <label>Standard</label>
      <term>1 year</term>
      <interest>4.49</interest>
    </rate>
  </standard>
</rss>
```

Mapping:
- `<lastupdated>` → parsed to ISO format with NZ timezone → `bank_last_updated`
- `<label>` → `product_name`
- `<term>` → `term`
- `<interest>` → `rate_percentage`

**BNZ Date Parsing:**
- Input format: "Thursday, 18 December 2025"
- Output format: "2025-12-18T00:00:00+13:00"
- Parser must handle NZ timezone (Pacific/Auckland)
- Other banks may have different formats requiring bank-specific parsers

## Repository Structure
```
/
├── .github/
│   └── workflows/
│       └── scrape.yml           # Daily cron job
├── src/
│   ├── bnz/                    # BNZ-specific scraper module
│   │   ├── __init__.py         # Exports scrape_bnz_rates
│   │   ├── extractor.py        # API key extraction from HTML
│   │   ├── parser.py           # XML parsing (rates + last_updated)
│   │   └── scraper.py          # BNZ scraping orchestration
│   ├── scraper.py              # Main entry point (calls bank scrapers)
│   ├── http.py                 # Shared HTTP utilities (fetch with retry)
│   ├── notifier.py             # ntfy.sh push notifications (bank-agnostic)
│   ├── storage.py              # JSON file operations (bank-agnostic)
│   └── html_generator.py       # Generate static HTML (bank-agnostic)
├── tests/
│   ├── fixtures/               # Test fixtures (HTML/XML samples)
│   ├── test_api_key_extractor.py
│   ├── test_bnz_parser.py
│   ├── test_http.py
│   ├── test_notifier.py
│   ├── test_storage.py
│   └── test_html_generator.py
├── data/
│   ├── bnz_rates.json          # BNZ historical rate data
│   ├── anz_rates.json          # ANZ historical rate data (future)
│   └── westpac_rates.json      # Westpac historical rate data (future)
├── docs/
│   └── index.html              # Auto-generated visualization (GitHub Pages)
├── pyproject.toml              # Project config and dependencies
├── uv.lock                     # Dependency lockfile
├── README.md                   # Project documentation
└── PROJECT_SPEC.md            # This file
```

## Technology Stack
- **Python 3.14** (latest stable version)
- **Package Manager**: uv for dependency/environment management
- **Libraries**:
  - `requests`: HTTP requests
  - `xml.etree.ElementTree`: XML parsing (stdlib, no extra dependency)
  - Standard library for JSON, regex, datetime, timezone handling
- **GitHub Actions**: CI/CD and scheduling
- **GitHub Pages**: Static hosting

## Cost Analysis
- **GitHub Actions**: Free (well under 2000 mins/month limit)
- **GitHub Pages**: Free
- **Storage**: Free (git repository)
- **Total**: $0/month

### Notifications (ntfy.sh)
- **Opt-in**: Set `NTFY_TOPIC` environment variable to enable push notifications on rate changes
- **Service**: Uses public ntfy.sh instance (no auth required, topic name acts as implicit password)
- **Trigger**: Sends notification only when rates actually change
- **Failure handling**: Notification errors print a warning but never break the scraping pipeline
- **GitHub Actions**: Set `NTFY_TOPIC` as a repository variable (`Settings > Secrets and variables > Actions > Variables`)
- **Local**: `NTFY_TOPIC=my-kiwi-rates uv run python -m src.scraper`

## Future Extensions
- Add other NZ banks (ANZ, Westpac, ASB, Kiwibank)
  - Each bank follows the pattern: `src/[bank]/extractor.py`, `parser.py`, `scraper.py`
  - Bank-agnostic code (`storage.py`, `html_generator.py`) remains shared
- Implement base class/interface for bank scrapers (optional, for code reuse)
- Enhanced HTML visualization (charts, trends)
- Email alerts on rate changes
- Historical rate comparison

## Bank Module Pattern
Each bank-specific module (e.g., `src/bnz/`) contains:

1. **`__init__.py`**: Exports the main scraper function (`scrape_bnz_rates`)
2. **`extractor.py`**: Extracts API key or authentication tokens from bank's HTML
3. **`parser.py`**: Parses bank-specific data format (XML, JSON, HTML, etc.)
4. **`scraper.py`**: Orchestrates the scraping process (fetch → parse → store)

**Shared utilities:**
- `src/http.py`: HTTP fetch with retry logic and exponential backoff
- `src/storage.py`: JSON file operations (load/save/compare rates)
- `src/html_generator.py`: Generates HTML from all bank data files
- `src/scraper.py`: Main entry point that calls individual bank scrapers

## Design Decisions

### Why JSON over SQLite?
- Simpler (no database library needed)
- Human-readable
- Git-friendly (easy diffs)
- Sufficient for append-only time-series data

### Why separate files per bank?
- Clean git diffs (BNZ updates don't touch ANZ file)
- Better scalability (avoids single large file)
- Easier debugging and maintenance per bank
- Simple extensibility (add bank = add file)
- Bank identified by filename (no redundant field in every record)

### Why stateful updates (only store changes)?
- Cleaner data - no redundant entries when rates don't change
- Smaller file sizes - only meaningful changes recorded
- Easy to visualize rate movements and trends
- Less git noise - commits only when rates actually change (no metadata-only updates)
- `bank_last_updated` provides validation of actual bank updates vs our scrapes
- Scraper health monitored via GitHub Actions failure notifications instead of git commits

### Why GitHub over AWS Lambda?
- Free vs. ~$1-5/month
- No AWS account complexity
- Built-in version control and backup
- Simpler deployment

### Why API extraction over stored key?
- Zero maintenance when API key rotates
- No secrets management needed
- API key is public anyway (in frontend)
- Only adds ~500ms overhead (acceptable for daily job)

### Why no Playwright/Selenium?
- API endpoint is available and stable
- Browser automation is overkill
- Slower, more complex, heavier dependencies
- Higher maintenance burden

## Implementation Details

### Scheduling
- **Frequency**: Once per day at 11 PM NZ time
- **Rationale**: Gives banks time to update websites during business day, captures all changes for that day
- **GitHub Actions cron**: `0 10 * * *` (10:00 UTC = 11:00 PM NZDT in summer, 10:00 PM NZST in winter - may need adjustment)

### Error Handling Strategy
- **Fail loudly**: All errors raise exceptions (no silent failures), with one intentional exception: the notification module (`notifier.py`) catches all errors and prints warnings, because notification failure must not break the scraping pipeline
- **Validation**: Empty results treated as errors (BNZ parser raises ValueError if no rates found)
- **Retry logic**: Network failures retry 5 times with exponential backoff
- **Workflow guards**: GitHub Actions won't commit on scraper failure (`if: success()` condition)
- **Monitoring**: Email notifications on workflow failures
- **Clear error messages**: JSON decode errors, date parsing failures, and missing data all raise descriptive errors

### Bootstrap/Initialization
- **Seed files**: User provides initial empty/seed JSON file for each bank
- **Keep simple**: No complex initialization logic
- **File structure**: Each bank file follows same schema

### Git Commit Strategy
- **Commit only on changes**: Only commit when rates actually change (creates cleaner git history)
- **Monitoring**: Scraper health tracked via GitHub Actions failure notifications (not git commits)
- **Commit message**: Simple, auto-generated (e.g., "Update BNZ rates - 2025-12-22")
- **Git config**: Use GitHub Actions bot identity

### Testing Approach
- **Unit tests**: Test parsers, comparison logic, date handling
- **No integration tests**: Don't call live APIs in tests
- **Static test files**: Use captured XML/HTML responses for testing
- **Validation automation**: Optional tool to verify static test files match current live endpoints
- **Test framework**: pytest (de facto standard)
- **Pre-push hook**: Optional git hook runs all tests before allowing push to prevent broken code

### HTML Visualization
- **Keep simple**: Show only latest rates per product/term
- **Format**: Basic HTML table with rate change indicators
- **Mobile responsive**: Card-based layout below 768px breakpoint for optimal mobile viewing
- **Rate changes**: Display how rates changed since previous scrape
  - Format: `5.55% (+0.26)` or `4.49% (-0.20)` or `4.49% (0.00)` for first appearance
  - Color coding: Red for increases (bad for borrowers), green for decreases (good), gray for no change
  - Comparison: Always compares the two most recent entries per product/term
- **Recent changes**: Rows with rate changes in last 14 days highlighted with yellow background
  - Visual distinction helps quickly identify recent market movements
  - Only applies to rates that actually changed (not zero-change entries)
- **New product indicator**: Products first appearing within last 30 days show blue "NEW" badge
  - Helps users quickly identify newly introduced loan products
  - Badge automatically disappears after 30 days
  - Can appear alongside recent change highlighting (yellow background + NEW badge)
- **Days since update**: Each rate's "Last Updated" column shows how many days since the rate was last updated
  - Format: `2026-02-03 (7d)` — date followed by days-ago indicator
  - Styled with `.days-ago` CSS class (gray, smaller font)
  - Always displayed for all rates, regardless of whether the rate changed
- **Date information**:
  - **Top header**: Shows "Last rate change: YYYY-MM-DD (Xd)" - the most recent date when any rate actually changed across all banks, with days-ago indicator styled with `.days-ago` CSS class
  - **Below each table**: Shows timestamp per bank:
    - "Page generated: YYYY-MM-DD HH:MM:SS" - when the HTML was generated (indicates scraper ran successfully)
  - If no rate changes detected, top header shows "No changes detected"
- **No charts**: Simple is sufficient for now
- **Data source**: Read all `data/*_rates.json` files, extract latest rate per product/term combo

## Implementation Status
- [x] Requirements gathering
- [x] Architecture design
- [x] Technology selection
- [x] Implementation details defined
- [x] Repository setup
- [x] Core scraper implementation (BNZ module with extractor, parser, scraper)
- [x] GitHub Actions workflow (configured for daily runs)
- [x] HTML generator (reads all bank files, generates static HTML)
- [x] Testing and validation (83 tests, all passing)
- [x] Code organization (bank-specific modules for easy extension)
- [x] Initial deployment (git repository initialized and pushed to GitHub)
- [x] First production run (successfully scraped BNZ rates on 2025-12-22)
- [x] Stateful updates bug fix (2026-02-04): Fixed duplicate rates issue - now only stores rates that actually changed via `filter_changed_rates()` function
- [x] Rate change display (2026-02-04): HTML visualization now shows rate changes since previous scrape with color-coded indicators (red=increase, green=decrease, gray=neutral)
- [x] Recent change highlighting (2026-02-04): Rows with rate changes in last 14 days now highlighted with yellow background for quick identification of recent market movements
- [x] New product indicator (2026-02-04): Products first appearing within 30 days show blue NEW badge for easy identification
- [x] Python upgrade (2026-02-05): Upgraded from Python 3.13 to 3.14 for latest features and security patches
- [x] Days since update indicator (2026-02-10): Added `(Xd)` indicator to "Last Updated" column showing days since each rate was last updated, and to the top "Last rate change" header
- [x] Push notifications (2026-02-17): ntfy.sh notifications on rate changes via `NTFY_TOPIC` env var (opt-in, silent no-op when unconfigured)
- [x] Error handling hardening (2026-02-05): Implemented fail-loudly error handling strategy:
  - GitHub Actions workflow guard prevents committing on scraper failure
  - Empty rates validation raises error instead of silent success
  - Removed bare except clauses - date parsing failures now propagate
  - JSON decode errors provide clear context messages
  - 83 comprehensive tests ensure reliability

## Notes
- User is experienced senior software engineer
- Test-driven development approach followed throughout
- All tests must be updated to follow changes
- Bank-specific code organized in separate modules (e.g., src/bnz/)
- Generic utilities (storage, html_generator) remain shared across banks
- Future banks should follow same pattern: src/[bank_name]/__init__.py, extractor.py, parser.py, scraper.py
