"""Main scraper orchestration."""
from pathlib import Path

from src.bnz import scrape_bnz_rates
from src.notifier import notify_rate_changes


def main():
    """Main entry point for scraper."""
    data_dir = Path(__file__).parent.parent / "data"
    bnz_file = data_dir / "bnz_rates.json"

    print("Starting BNZ rates scraper...")

    try:
        result = scrape_bnz_rates(bnz_file)
        print(f"✓ Scraping completed successfully")
        print(f"  Rates changed: {result['rates_changed']}")
        print(f"  Number of rates: {result['num_rates']}")
        print(f"  Scraped at: {result['scraped_at']}")
        if result["rates_changed"]:
            notify_rate_changes(
                bank_name="BNZ",
                changed_rates=result["changed_rates"],
                existing_rates=result["existing_rates"],
            )
    except Exception as e:
        print(f"✗ Scraping failed: {e}")
        raise


if __name__ == "__main__":
    main()
