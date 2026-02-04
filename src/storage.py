"""Storage module for rate data."""
import json
from pathlib import Path


def load_rates(file_path: Path) -> dict:
    """
    Load rates from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary with last_scraped, bank_last_updated, and rates
    """
    if not file_path.exists():
        return {
            "last_scraped": None,
            "bank_last_updated": None,
            "rates": []
        }

    with open(file_path) as f:
        return json.load(f)


def save_rates(file_path: Path, data: dict) -> None:
    """
    Save rates to JSON file.

    Args:
        file_path: Path to JSON file
        data: Dictionary with last_scraped, bank_last_updated, and rates
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def should_update_rates(existing_rates: list[dict], new_rates: list[dict]) -> bool:
    """
    Determine if rates have changed and should be updated.

    Compares the latest rates in existing_rates with new_rates to see if
    any product/term combination has a different rate or if products were
    added/removed.

    Args:
        existing_rates: List of existing rate entries (with scraped_at timestamps)
        new_rates: List of new rate entries (without scraped_at timestamps)

    Returns:
        True if rates should be updated, False otherwise
    """
    if not existing_rates:
        return bool(new_rates)  # Update if we have new rates and nothing exists

    # Build a map of latest rates per product/term from existing data
    latest_existing = {}
    for rate in existing_rates:
        key = (rate["product_name"], rate["term"])
        # Keep the most recent entry (assuming list is chronological)
        latest_existing[key] = rate["rate_percentage"]

    # Build a map of new rates per product/term
    new_rates_map = {}
    for rate in new_rates:
        key = (rate["product_name"], rate["term"])
        new_rates_map[key] = rate["rate_percentage"]

    # Check if rates are different
    return latest_existing != new_rates_map


def filter_changed_rates(existing_rates: list[dict], new_rates: list[dict]) -> list[dict]:
    """
    Filter new rates to only include those that have changed.

    Returns only rates that:
    - Are new products/terms (not in existing data)
    - Have different rate_percentage values from latest existing entry

    Args:
        existing_rates: List of existing rate entries (with scraped_at timestamps)
        new_rates: List of new rate entries (without scraped_at timestamps)

    Returns:
        List of rates that have changed (preserves order from new_rates)
    """
    # Build map of latest existing rates
    latest_existing = {}
    for rate in existing_rates:
        key = (rate["product_name"], rate["term"])
        latest_existing[key] = rate["rate_percentage"]

    # Filter to only changed rates
    changed_rates = []
    for rate in new_rates:
        key = (rate["product_name"], rate["term"])
        if key not in latest_existing or latest_existing[key] != rate["rate_percentage"]:
            changed_rates.append(rate)

    return changed_rates
