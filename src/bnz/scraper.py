"""BNZ rates scraper."""
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from src.bnz.extractor import extract_api_key
from src.bnz.parser import parse_last_updated, parse_rates
from src.storage import load_rates, save_rates, should_update_rates


def fetch_with_retry(url: str, headers: dict | None = None, max_retries: int = 3, backoff: float = 1.0) -> requests.Response:
    """
    Fetch URL with retry logic and exponential backoff.

    Args:
        url: URL to fetch
        headers: Optional headers dictionary
        max_retries: Maximum number of retry attempts
        backoff: Initial backoff time in seconds (doubles each retry)

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            last_exception = e
            if attempt < max_retries - 1:
                sleep_time = backoff * (2 ** attempt)
                time.sleep(sleep_time)

    raise last_exception


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
    html_response = fetch_with_retry(html_url)
    api_key = extract_api_key(html_response.text)

    # Fetch rates XML using extracted API key
    rates_url = "https://api.bnz.co.nz/v1/ratesfeed/home/xml"
    headers = {
        "apikey": api_key,
        "Accept": "application/xml, text/xml",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.bnz.co.nz/",
        "Origin": "https://www.bnz.co.nz",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
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
        # Add scraped_at timestamp to new rates
        for rate in new_rates:
            rate["scraped_at"] = now_iso

        # Append new rates to existing
        updated_rates = existing_data["rates"] + new_rates
    else:
        # Keep existing rates
        updated_rates = existing_data["rates"]

    # Update metadata
    updated_data = {
        "last_scraped": now_iso,
        "bank_last_updated": bank_last_updated.isoformat(),
        "rates": updated_rates
    }

    # Save to file
    save_rates(data_file, updated_data)

    return {
        "success": True,
        "rates_changed": rates_changed,
        "num_rates": len(new_rates),
        "scraped_at": now_iso
    }
