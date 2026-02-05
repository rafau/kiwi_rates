"""Tests for HTML generator."""
import json
from pathlib import Path

import pytest

from src.html_generator import generate_html, extract_latest_rates


@pytest.fixture
def sample_bnz_data(tmp_path):
    """Create sample BNZ data file."""
    data = {
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
                "product_name": "Standard",
                "term": "Variable",
                "rate_percentage": 5.84
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.39  # Updated rate
            }
        ]
    }

    file_path = tmp_path / "bnz_rates.json"
    file_path.write_text(json.dumps(data, indent=2))
    return file_path


def test_extract_latest_rates(sample_bnz_data):
    """Test extracting latest rates from data file."""
    latest = extract_latest_rates(sample_bnz_data)

    # Should have 2 unique product/term combinations
    assert len(latest) == 2

    # Check that we got the most recent rate for Standard 1 year
    standard_1y = next(r for r in latest if r["product_name"] == "Standard" and r["term"] == "1 year")
    assert standard_1y["rate_percentage"] == 4.39  # Most recent value
    assert standard_1y["scraped_at"] == "2025-12-20T12:00:00+13:00"
    assert "rate_change" in standard_1y
    assert standard_1y["rate_change"] == -0.10  # 4.39 - 4.49 = -0.10

    # Check Variable rate
    standard_var = next(r for r in latest if r["product_name"] == "Standard" and r["term"] == "Variable")
    assert standard_var["rate_percentage"] == 5.84
    assert "rate_change" in standard_var
    assert standard_var["rate_change"] == 0.00  # Only one entry


def test_extract_latest_rates_empty_file(tmp_path):
    """Test extracting from empty data file."""
    empty_data = {
        "bank_last_updated": None,
        "rates": []
    }

    file_path = tmp_path / "empty_rates.json"
    file_path.write_text(json.dumps(empty_data))

    latest = extract_latest_rates(file_path)
    assert latest == []


def test_generate_html(tmp_path, sample_bnz_data):
    """Test generating HTML from data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Copy sample data to data dir with proper name
    (data_dir / "bnz_rates.json").write_text(sample_bnz_data.read_text())

    output_file = tmp_path / "index.html"

    generate_html(data_dir, output_file)

    # Verify file was created
    assert output_file.exists()

    html_content = output_file.read_text()

    # Check for key elements
    assert "<html" in html_content.lower()
    assert "<table" in html_content.lower()
    assert "BNZ" in html_content
    assert "Standard" in html_content
    assert "1 year" in html_content
    assert "4.39" in html_content  # Latest rate
    assert "Variable" in html_content
    assert "5.84" in html_content

    # Check for "Last rate change:" at top (instead of "Last updated:")
    assert "Last rate change:" in html_content

    # Check for dates section below table
    assert "Page generated:" in html_content
    assert "bank-dates" in html_content


def test_generate_html_multiple_banks(tmp_path):
    """Test generating HTML with multiple banks."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create BNZ data
    bnz_data = {
        "bank_last_updated": "2025-12-18T00:00:00+13:00",
        "rates": [
            {
                "scraped_at": "2025-12-22T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    # Create ANZ data
    anz_data = {
        "bank_last_updated": "2025-12-18T00:00:00+13:00",
        "rates": [
            {
                "scraped_at": "2025-12-22T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.59
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))
    (data_dir / "anz_rates.json").write_text(json.dumps(anz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Should contain both banks
    assert "BNZ" in html_content
    assert "ANZ" in html_content
    assert "4.49" in html_content
    assert "4.59" in html_content

    # Each bank should have its own dates section
    assert html_content.count("Page generated:") == 2
    assert html_content.count("bank-dates") >= 2


def test_extract_latest_rates_with_rate_increase(tmp_path):
    """Test extracting rates when rate increases."""
    data = {
        "bank_last_updated": "2025-12-18T00:00:00+13:00",
        "rates": [
            {
                "scraped_at": "2025-12-15T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.59
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.59
    assert "rate_change" in rate
    assert rate["rate_change"] == 0.10


def test_extract_latest_rates_with_rate_decrease(tmp_path):
    """Test extracting rates when rate decreases."""
    data = {
        "bank_last_updated": "2025-12-18T00:00:00+13:00",
        "rates": [
            {
                "scraped_at": "2025-12-15T12:00:00+13:00",
                "product_name": "Standard",
                "term": "6 months",
                "rate_percentage": 4.69
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "6 months",
                "rate_percentage": 4.49
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.49
    assert "rate_change" in rate
    assert rate["rate_change"] == -0.20


def test_extract_latest_rates_single_entry(tmp_path):
    """Test extracting rates when only one entry exists."""
    data = {
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

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.49
    assert "rate_change" in rate
    assert rate["rate_change"] == 0.00


def test_extract_latest_rates_no_change(tmp_path):
    """Test extracting rates when rate doesn't change."""
    data = {
        "bank_last_updated": "2025-12-18T00:00:00+13:00",
        "rates": [
            {
                "scraped_at": "2025-12-15T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.49
    assert "rate_change" in rate
    assert rate["rate_change"] == 0.00


def test_extract_latest_rates_multiple_changes(tmp_path):
    """Test extracting rates with multiple changes - should compare last two."""
    data = {
        "bank_last_updated": "2025-12-18T00:00:00+13:00",
        "rates": [
            {
                "scraped_at": "2025-12-10T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 5.00
            },
            {
                "scraped_at": "2025-12-15T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.59
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.59
    assert "rate_change" in rate
    # Should be 4.59 - 4.49 = 0.10 (not comparing to 5.00)
    assert rate["rate_change"] == 0.10


def test_generate_html_includes_rate_changes(tmp_path):
    """Test that generated HTML includes rate change indicators."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create data with rate changes
    bnz_data = {
        "bank_last_updated": "2025-12-18T00:00:00+13:00",
        "rates": [
            {
                "scraped_at": "2025-12-15T12:00:00+13:00",
                "product_name": "Standard",
                "term": "6 months",
                "rate_percentage": 4.69
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "6 months",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": "2025-12-15T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.59
            },
            {
                "scraped_at": "2025-12-20T12:00:00+13:00",
                "product_name": "Standard",
                "term": "2 years",
                "rate_percentage": 5.00
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Check for rate decrease (green, good for borrowers)
    assert "(-0.20)" in html_content
    assert "rate-change-negative" in html_content

    # Check for rate increase (red, bad for borrowers)
    assert "(+0.10)" in html_content
    assert "rate-change-positive" in html_content

    # Check for single entry (neutral/gray)
    assert "(0.00)" in html_content
    assert "rate-change-neutral" in html_content

    # Verify CSS classes exist
    assert ".rate-change-positive" in html_content
    assert ".rate-change-negative" in html_content
    assert ".rate-change-neutral" in html_content


def test_extract_latest_rates_with_recent_change(tmp_path):
    """Test that recent rate changes (< 14 days) are marked as recent."""
    from datetime import datetime, timedelta, timezone

    # Create a date 7 days ago (recent change)
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": fourteen_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": seven_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.75
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.75
    assert rate["rate_change"] == 0.26  # 4.75 - 4.49
    assert "is_recent_change" in rate
    assert rate["is_recent_change"] is True


def test_extract_latest_rates_with_old_change(tmp_path):
    """Test that old rate changes (> 14 days) are not marked as recent."""
    from datetime import datetime, timedelta, timezone

    # Create a date 20 days ago (old change)
    now = datetime.now(timezone.utc)
    twenty_days_ago = now - timedelta(days=20)
    thirty_days_ago = now - timedelta(days=30)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": thirty_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": twenty_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.69
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.69
    assert rate["rate_change"] == 0.20  # 4.69 - 4.49
    assert "is_recent_change" in rate
    assert rate["is_recent_change"] is False


def test_extract_latest_rates_no_change_not_recent(tmp_path):
    """Test that entries with no rate change are not marked as recent."""
    from datetime import datetime, timedelta, timezone

    # Create a date 5 days ago (recent, but no change)
    now = datetime.now(timezone.utc)
    five_days_ago = now - timedelta(days=5)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": five_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["rate_percentage"] == 4.49
    assert rate["rate_change"] == 0.00  # Only one entry
    assert "is_recent_change" in rate
    assert rate["is_recent_change"] is False


def test_generate_html_includes_recent_change_class(tmp_path):
    """Test that HTML includes recent-change class for recent rate changes."""
    from datetime import datetime, timedelta, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create data with recent change (7 days ago)
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": fourteen_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": seven_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.75
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify recent-change class is present
    assert 'class="recent-change"' in html_content

    # Verify CSS class is defined
    assert ".recent-change" in html_content


def test_generate_html_excludes_recent_change_for_old(tmp_path):
    """Test that HTML excludes recent-change class for old rate changes."""
    from datetime import datetime, timedelta, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create data with old change (20 days ago)
    now = datetime.now(timezone.utc)
    twenty_days_ago = now - timedelta(days=20)
    thirty_days_ago = now - timedelta(days=30)

    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": thirty_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": twenty_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.69
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify recent-change class is NOT present for this old change
    # Note: We need to check that the row with old change doesn't have the class
    # Since we only have one rate entry, and it's old, there should be no recent-change class
    assert html_content.count('class="recent-change"') == 0


def test_extract_latest_rates_new_product_within_30_days(tmp_path):
    """Test that products first appearing within 30 days are marked as new."""
    from datetime import datetime, timedelta, timezone

    # Create a product that first appeared 15 days ago
    now = datetime.now(timezone.utc)
    fifteen_days_ago = now - timedelta(days=15)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": fifteen_days_ago.isoformat(),
                "product_name": "NewProduct",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["product_name"] == "NewProduct"
    assert "is_new_product" in rate
    assert rate["is_new_product"] is True
    assert "days_since_first_appearance" in rate
    assert rate["days_since_first_appearance"] == 15


def test_extract_latest_rates_old_product_over_30_days(tmp_path):
    """Test that products first appearing over 30 days ago are NOT marked as new."""
    from datetime import datetime, timedelta, timezone

    # Create a product that first appeared 48 days ago
    now = datetime.now(timezone.utc)
    forty_eight_days_ago = now - timedelta(days=48)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": forty_eight_days_ago.isoformat(),
                "product_name": "OldProduct",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["product_name"] == "OldProduct"
    assert "is_new_product" in rate
    assert rate["is_new_product"] is False
    assert "days_since_first_appearance" in rate
    assert rate["days_since_first_appearance"] == 48


def test_extract_latest_rates_exactly_30_days(tmp_path):
    """Test boundary condition: product exactly 30 days old is NOT marked as new."""
    from datetime import datetime, timedelta, timezone

    # Create a product that first appeared exactly 30 days ago
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": thirty_days_ago.isoformat(),
                "product_name": "BoundaryProduct",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["product_name"] == "BoundaryProduct"
    assert "is_new_product" in rate
    assert rate["is_new_product"] is False
    assert "days_since_first_appearance" in rate
    assert rate["days_since_first_appearance"] == 30


def test_extract_latest_rates_new_product_with_rate_changes(tmp_path):
    """Test that new product with multiple rate changes uses earliest scraped_at date."""
    from datetime import datetime, timedelta, timezone

    # Create a product that first appeared 20 days ago, with rate changes
    now = datetime.now(timezone.utc)
    twenty_days_ago = now - timedelta(days=20)
    ten_days_ago = now - timedelta(days=10)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": twenty_days_ago.isoformat(),
                "product_name": "NewChangingProduct",
                "term": "2 years",
                "rate_percentage": 5.00
            },
            {
                "scraped_at": ten_days_ago.isoformat(),
                "product_name": "NewChangingProduct",
                "term": "2 years",
                "rate_percentage": 5.15
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["product_name"] == "NewChangingProduct"
    assert rate["rate_percentage"] == 5.15  # Latest rate
    assert "is_new_product" in rate
    assert rate["is_new_product"] is True  # Based on earliest date (20 days)
    assert "days_since_first_appearance" in rate
    assert rate["days_since_first_appearance"] == 20


def test_extract_latest_rates_new_and_recent_change(tmp_path):
    """Test that product can be both new AND have recent rate change."""
    from datetime import datetime, timedelta, timezone

    # Create a new product (first appeared 25 days ago) with recent rate change (5 days ago)
    now = datetime.now(timezone.utc)
    twenty_five_days_ago = now - timedelta(days=25)
    five_days_ago = now - timedelta(days=5)

    data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": twenty_five_days_ago.isoformat(),
                "product_name": "NewRecentProduct",
                "term": "1 year",
                "rate_percentage": 4.50
            },
            {
                "scraped_at": five_days_ago.isoformat(),
                "product_name": "NewRecentProduct",
                "term": "1 year",
                "rate_percentage": 4.75
            }
        ]
    }

    file_path = tmp_path / "test_rates.json"
    file_path.write_text(json.dumps(data))

    latest = extract_latest_rates(file_path)

    assert len(latest) == 1
    rate = latest[0]
    assert rate["product_name"] == "NewRecentProduct"
    assert "is_new_product" in rate
    assert rate["is_new_product"] is True
    assert "is_recent_change" in rate
    assert rate["is_recent_change"] is True
    assert rate["rate_change"] == 0.25


def test_generate_html_includes_new_product_badge(tmp_path):
    """Test that HTML includes NEW badge and CSS for new products."""
    from datetime import datetime, timedelta, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create data with new product (15 days ago)
    now = datetime.now(timezone.utc)
    fifteen_days_ago = now - timedelta(days=15)

    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": fifteen_days_ago.isoformat(),
                "product_name": "NewProduct",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify NEW badge is present
    assert "new-product-badge" in html_content
    assert ">New</span>" in html_content

    # Verify CSS class is defined
    assert ".new-product-badge" in html_content


def test_generate_html_excludes_new_badge_for_old_products(tmp_path):
    """Test that HTML excludes NEW badge for products over 30 days old."""
    from datetime import datetime, timedelta, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create data with old product (48 days ago)
    now = datetime.now(timezone.utc)
    forty_eight_days_ago = now - timedelta(days=48)

    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": forty_eight_days_ago.isoformat(),
                "product_name": "OldProduct",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify NEW badge is NOT present (CSS class should exist but not be used)
    # Check that the product name doesn't have the badge
    assert "OldProduct" in html_content
    # The new-product-badge CSS class should be defined (in desktop + mobile CSS)
    assert ".new-product-badge" in html_content
    # But it should not be used in this table (no actual badge instances)
    assert html_content.count("new-product-badge") == 2  # Only in CSS definitions (desktop + mobile)


def test_generate_html_new_product_with_recent_change_styling(tmp_path):
    """Test that both yellow background AND NEW badge render correctly together."""
    from datetime import datetime, timedelta, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create new product (25 days ago) with recent rate change (5 days ago)
    now = datetime.now(timezone.utc)
    twenty_five_days_ago = now - timedelta(days=25)
    five_days_ago = now - timedelta(days=5)

    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": twenty_five_days_ago.isoformat(),
                "product_name": "NewRecentProduct",
                "term": "1 year",
                "rate_percentage": 4.50
            },
            {
                "scraped_at": five_days_ago.isoformat(),
                "product_name": "NewRecentProduct",
                "term": "1 year",
                "rate_percentage": 4.75
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify both features are present
    assert "new-product-badge" in html_content
    assert ">New</span>" in html_content
    assert 'class="recent-change"' in html_content

    # Verify the row has recent-change class
    # And the product name has NEW badge
    assert "NewRecentProduct" in html_content


def test_generate_html_includes_dates_section(tmp_path):
    """Test that HTML includes dates section with correct structure."""
    from datetime import datetime, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    now = datetime.now(timezone.utc)

    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": now.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify dates section structure
    assert 'class="bank-dates"' in html_content
    assert "Page generated:" in html_content

    # Verify CSS class is defined
    assert ".bank-dates" in html_content


def test_generate_html_last_rate_change_header(tmp_path):
    """Test that top header shows 'Last rate change' with date."""
    from datetime import datetime, timedelta, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": fourteen_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": seven_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.75
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify "Last rate change:" header exists
    assert "Last rate change:" in html_content

    # Should not contain old "Last updated:"
    assert "Last updated:" not in html_content


def test_generate_html_last_rate_change_no_changes(tmp_path):
    """Test scenario where rates array has no changes."""
    from datetime import datetime, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    now = datetime.now(timezone.utc)

    # Only one entry per product (no changes)
    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": now.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Should show "No changes detected" or similar
    assert "Last rate change:" in html_content
    assert ("No changes detected" in html_content or "N/A" in html_content)


def test_get_most_recent_rate_change():
    """Test helper function get_most_recent_rate_change."""
    from datetime import datetime, timedelta, timezone
    from src.html_generator import get_most_recent_rate_change

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # Test with multiple rates with changes
    rates = [
        {
            "scraped_at": fourteen_days_ago.isoformat(),
            "rate_change": 0.10
        },
        {
            "scraped_at": seven_days_ago.isoformat(),
            "rate_change": 0.20
        }
    ]
    result = get_most_recent_rate_change(rates)
    assert result is not None
    assert seven_days_ago.strftime("%Y-%m-%d") in result

    # Test with all rates having no changes
    rates_no_change = [
        {
            "scraped_at": fourteen_days_ago.isoformat(),
            "rate_change": 0.00
        },
        {
            "scraped_at": seven_days_ago.isoformat(),
            "rate_change": 0.00
        }
    ]
    result = get_most_recent_rate_change(rates_no_change)
    assert result is None

    # Test with empty rates list
    result = get_most_recent_rate_change([])
    assert result is None

    # Test mixed scenario
    rates_mixed = [
        {
            "scraped_at": fourteen_days_ago.isoformat(),
            "rate_change": 0.10
        },
        {
            "scraped_at": seven_days_ago.isoformat(),
            "rate_change": 0.00
        }
    ]
    result = get_most_recent_rate_change(rates_mixed)
    assert result is not None
    assert fourteen_days_ago.strftime("%Y-%m-%d") in result


def test_generate_html_multiple_banks_global_last_change(tmp_path):
    """Test that top header shows most recent change across all banks."""
    from datetime import datetime, timedelta, timezone

    data_dir = tmp_path / "data"
    data_dir.mkdir()

    now = datetime.now(timezone.utc)
    five_days_ago = now - timedelta(days=5)
    ten_days_ago = now - timedelta(days=10)
    twenty_days_ago = now - timedelta(days=20)

    # BNZ has an older change (10 days ago)
    bnz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": twenty_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            },
            {
                "scraped_at": ten_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.59
            }
        ]
    }

    # ANZ has a newer change (5 days ago)
    anz_data = {
        "bank_last_updated": now.isoformat(),
        "rates": [
            {
                "scraped_at": twenty_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.39
            },
            {
                "scraped_at": five_days_ago.isoformat(),
                "product_name": "Standard",
                "term": "1 year",
                "rate_percentage": 4.49
            }
        ]
    }

    (data_dir / "bnz_rates.json").write_text(json.dumps(bnz_data))
    (data_dir / "anz_rates.json").write_text(json.dumps(anz_data))

    output_file = tmp_path / "index.html"
    generate_html(data_dir, output_file)

    html_content = output_file.read_text()

    # Verify top header shows "Last rate change:"
    assert "Last rate change:" in html_content

    # The date should be from the most recent change (5 days ago = ANZ)
    # Format: YYYY-MM-DD
    expected_date = five_days_ago.strftime("%Y-%m-%d")
    assert expected_date in html_content


def test_get_most_recent_rate_change_invalid_date_raises_error():
    """Test that malformed dates in rate data raise errors instead of being silently caught."""
    from src.html_generator import get_most_recent_rate_change

    rates = [
        {
            "scraped_at": "INVALID DATE FORMAT",
            "rate_change": 0.10
        }
    ]

    with pytest.raises(ValueError):
        get_most_recent_rate_change(rates)


def test_generate_html_content_invalid_date_raises_error(tmp_path):
    """Test that HTML generation fails loudly with malformed date instead of silently handling it."""
    from src.html_generator import generate_html_content

    # Data with malformed date
    bank_data = {
        "BNZ": {
            "rates": [
                {
                    "scraped_at": "NOT A VALID DATE",
                    "product_name": "Standard",
                    "term": "1 year",
                    "rate_percentage": 4.49,
                    "rate_change": 0.00,
                    "is_recent_change": False,
                    "is_new_product": False
                }
            ]
        }
    }

    with pytest.raises(ValueError):
        generate_html_content(bank_data, None)
