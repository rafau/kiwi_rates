"""Tests for rate storage module."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.storage import load_rates, save_rates, should_update_rates


@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file."""
    file_path = tmp_path / "test_rates.json"
    return file_path


@pytest.fixture
def sample_rates_data():
    """Sample rates data for testing."""
    return {
        "last_scraped": "2025-12-20T12:00:00+13:00",
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
        "last_scraped": None,
        "bank_last_updated": None,
        "rates": []
    }


def test_save_rates(temp_json_file):
    """Test saving rates to file."""
    data = {
        "last_scraped": "2025-12-22T12:00:00+13:00",
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
