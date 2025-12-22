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
  "last_scraped": "2025-12-22T12:00:00+13:00",
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
- `last_scraped`: ISO timestamp with NZ timezone - when our scraper last ran (always updated, even if no rate changes)
- `bank_last_updated`: ISO timestamp with NZ timezone - when bank claims rates were last updated (null if bank doesn't provide this data)

### Rate Entry Fields
- `scraped_at`: ISO timestamp with NZ timezone - when this rate value was first scraped
- `product_name`: Product/loan type (e.g., "Standard", "TotalMoney", "BNZ Advantage")
- `term`: Loan term (e.g., "Variable", "6 months", "1 year", "2 years")
- `rate_percentage`: Interest rate as decimal

### Storage Strategy
- **Stateful updates**: Only append new entries to `rates` array when values actually change
- **Always update**: `last_scraped` updated on every run (proves scraper is working)
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
│   ├── storage.py              # JSON file operations (bank-agnostic)
│   └── html_generator.py       # Generate static HTML (bank-agnostic)
├── tests/
│   ├── fixtures/               # Test fixtures (HTML/XML samples)
│   ├── test_api_key_extractor.py
│   ├── test_bnz_parser.py
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
- **Python 3.13** (latest stable version)
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
- Less git noise - commits only when rates actually change
- `last_scraped` field ensures we can detect if scraper stops working
- `bank_last_updated` provides validation of actual bank updates vs our scrapes

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

### Error Handling
- **Retry logic**: Retry failed requests a few times (e.g., 3 attempts with exponential backoff)
- **Budget awareness**: Keep total runtime low to avoid consuming GitHub Actions free tier
- **Failure behavior**: Log error but don't crash - allow workflow to complete

### Bootstrap/Initialization
- **Seed files**: User provides initial empty/seed JSON file for each bank
- **Keep simple**: No complex initialization logic
- **File structure**: Each bank file follows same schema

### Git Commit Strategy
- **Always commit**: Yes, even if no rate changes (needed to preserve `last_scraped` timestamp)
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
- **Format**: Basic HTML table
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
- [x] Testing and validation (23 tests, all passing)
- [x] Code organization (bank-specific modules for easy extension)
- [x] Initial deployment (git repository initialized and pushed to GitHub)
- [x] First production run (successfully scraped BNZ rates on 2025-12-22)

## Notes
- User is experienced senior software engineer
- Test-driven development approach followed throughout
- All tests must be updated to follow changes
- Bank-specific code organized in separate modules (e.g., src/bnz/)
- Generic utilities (storage, html_generator) remain shared across banks
- Future banks should follow same pattern: src/[bank_name]/__init__.py, extractor.py, parser.py, scraper.py
