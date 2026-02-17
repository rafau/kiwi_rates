"""BNZ rates scraper."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.bnz.extractor import extract_api_key
from src.bnz.parser import parse_last_updated, parse_rates
from src.http import fetch_with_retry
from src.storage import load_rates, save_rates, should_update_rates, filter_changed_rates


def scrape_bnz_rates(data_file: Path) -> dict:
    """
    Scrape BNZ rates and update data file.

    Args:
        data_file: Path to BNZ rates JSON file

    Returns:
        Dictionary with status information

    Raises:
        Exception: If scraping fails
    """
    # Fetch HTML page to extract API key
    html_url = "https://www.bnz.co.nz/personal-banking/home-loans/compare-bnz-home-loan-rates"
    html_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    html_response = fetch_with_retry(html_url, headers=html_headers)
    api_key = extract_api_key(html_response.text)

    # Fetch rates XML using extracted API key
    rates_url = "https://api.bnz.co.nz/v1/ratesfeed/home/xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0",
        "Accept": "application/xml, text/xml",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Referer": "https://www.bnz.co.nz/",
        "apikey": api_key,
        "Origin": "https://www.bnz.co.nz",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Priority": "u=4",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    rates_response = fetch_with_retry(rates_url, headers=headers)

    # Parse XML
    bank_last_updated = parse_last_updated(rates_response.text)
    new_rates = parse_rates(rates_response.text)

    # Load existing data
    existing_data = load_rates(data_file)

    # Current timestamp in NZ timezone
    now = datetime.now(ZoneInfo("Pacific/Auckland"))
    now_iso = now.isoformat()

    # Check if rates changed
    rates_changed = should_update_rates(existing_data["rates"], new_rates)

    if rates_changed:
        # Filter to only rates that actually changed
        changed_rates = filter_changed_rates(existing_data["rates"], new_rates)

        # Add scraped_at timestamp to changed rates only
        for rate in changed_rates:
            rate["scraped_at"] = now_iso

        # Append only changed rates to existing
        updated_rates = existing_data["rates"] + changed_rates
    else:
        # Keep existing rates
        updated_rates = existing_data["rates"]

    # Update metadata
    updated_data = {
        "bank_last_updated": bank_last_updated.isoformat(),
        "rates": updated_rates
    }

    # Save to file
    save_rates(data_file, updated_data)

    return {
        "success": True,
        "rates_changed": rates_changed,
        "num_rates": len(new_rates),
        "scraped_at": now_iso,
        "changed_rates": changed_rates if rates_changed else [],
        "existing_rates": existing_data["rates"] if rates_changed else [],
    }
