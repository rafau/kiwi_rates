"""Tests for rate storage module."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.storage import load_rates, save_rates, should_update_rates, filter_changed_rates


@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file."""
    file_path = tmp_path / "test_rates.json"
    return file_path


@pytest.fixture
def sample_rates_data():
    """Sample rates data for testing."""
    return {
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
            }
        ]
    }


def test_load_rates_existing_file(temp_json_file, sample_rates_data):
    """Test loading rates from existing file."""
    temp_json_file.write_text(json.dumps(sample_rates_data, indent=2))

    result = load_rates(temp_json_file)

    assert result == sample_rates_data


def test_load_rates_nonexistent_file(temp_json_file):
    """Test loading rates from nonexistent file returns empty structure."""
    result = load_rates(temp_json_file)

    assert result == {
        "bank_last_updated": None,
        "rates": []
    }


def test_save_rates(temp_json_file):
    """Test saving rates to file."""
    data = {
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

    save_rates(temp_json_file, data)

    # Verify file was created with correct content
    assert temp_json_file.exists()
    loaded = json.loads(temp_json_file.read_text())
    assert loaded == data


def test_should_update_rates_empty_existing():
    """Test should update when existing rates are empty."""
    existing_rates = []
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        }
    ]

    result = should_update_rates(existing_rates, new_rates)

    assert result is True


def test_should_update_rates_changed():
    """Test should update when rates have changed."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.29  # Changed!
        }
    ]

    result = should_update_rates(existing_rates, new_rates)

    assert result is True


def test_should_update_rates_unchanged():
    """Test should not update when rates haven't changed."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49  # Same!
        }
    ]

    result = should_update_rates(existing_rates, new_rates)

    assert result is False


def test_should_update_rates_new_product():
    """Test should update when new product added."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "product_name": "Standard",
            "term": "2 years",  # New term!
            "rate_percentage": 4.69
        }
    ]

    result = should_update_rates(existing_rates, new_rates)

    assert result is True


def test_should_update_rates_product_removed():
    """Test should update when product removed."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.69
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        }
        # 2 years term removed!
    ]

    result = should_update_rates(existing_rates, new_rates)

    assert result is True


def test_filter_changed_rates_empty_existing():
    """Test filter returns all new rates when starting fresh."""
    existing_rates = []
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.69
        }
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    assert result == new_rates
    assert len(result) == 2


def test_filter_changed_rates_all_unchanged():
    """Test filter returns empty list when nothing changed."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.69
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49  # Same
        },
        {
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.69  # Same
        }
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    assert result == []
    assert len(result) == 0


def test_filter_changed_rates_partial_change():
    """Test filter returns only changed rate when 3 rates but 1 changed."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.69
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "TotalMoney",
            "term": "Variable",
            "rate_percentage": 5.84
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49  # Same
        },
        {
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.79  # Changed!
        },
        {
            "product_name": "TotalMoney",
            "term": "Variable",
            "rate_percentage": 5.84  # Same
        }
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    assert len(result) == 1
    assert result[0]["product_name"] == "Standard"
    assert result[0]["term"] == "2 years"
    assert result[0]["rate_percentage"] == 4.79


def test_filter_changed_rates_new_product_added():
    """Test filter returns new product/term that didn't exist before."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49  # Same
        },
        {
            "product_name": "Standard",
            "term": "2 years",  # New!
            "rate_percentage": 4.69
        }
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    assert len(result) == 1
    assert result[0]["product_name"] == "Standard"
    assert result[0]["term"] == "2 years"
    assert result[0]["rate_percentage"] == 4.69


def test_filter_changed_rates_product_removed():
    """Test filter returns empty list when product is removed from new rates."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.69
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49  # Same
        }
        # 2 years term removed from new rates (bank discontinued it)
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    # Removal is implicit - removed products don't appear in new_rates
    # so they won't be in filtered results either (correct behavior)
    assert result == []


def test_filter_changed_rates_multiple_changes():
    """Test filter returns multiple changed rates."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "6 months",
            "rate_percentage": 4.69
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "4 years",
            "rate_percentage": 5.29
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "6 months",
            "rate_percentage": 4.49  # Changed!
        },
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49  # Same
        },
        {
            "product_name": "Standard",
            "term": "4 years",
            "rate_percentage": 5.55  # Changed!
        }
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    assert len(result) == 2
    # Check both changed rates are present
    terms = [r["term"] for r in result]
    assert "6 months" in terms
    assert "4 years" in terms


def test_filter_changed_rates_preserves_order():
    """Test filter preserves input order of new_rates."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.69
        },
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "3 years",
            "rate_percentage": 4.89
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49  # Same
        },
        {
            "product_name": "Standard",
            "term": "2 years",
            "rate_percentage": 4.79  # Changed!
        },
        {
            "product_name": "Standard",
            "term": "3 years",
            "rate_percentage": 4.99  # Changed!
        }
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    assert len(result) == 2
    # Check order is preserved (2 years before 3 years)
    assert result[0]["term"] == "2 years"
    assert result[1]["term"] == "3 years"


def test_filter_changed_rates_handles_duplicates_in_existing():
    """Test filter uses latest existing entry when duplicates exist."""
    existing_rates = [
        {
            "scraped_at": "2025-12-15T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.49
        },
        {
            "scraped_at": "2025-12-16T12:00:00+13:00",
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.59  # Latest entry for this product/term
        }
    ]
    new_rates = [
        {
            "product_name": "Standard",
            "term": "1 year",
            "rate_percentage": 4.59  # Same as latest existing
        }
    ]

    result = filter_changed_rates(existing_rates, new_rates)

    # Should compare against latest (4.59), so no change detected
    assert result == []


def test_load_rates_corrupt_json_raises_error(temp_json_file):
    """Test that corrupt JSON file raises ValueError with clear context."""
    # Write invalid JSON to file
    temp_json_file.write_text("{invalid json content")

    with pytest.raises(ValueError, match=f"Failed to parse JSON from {temp_json_file}"):
        load_rates(temp_json_file)
