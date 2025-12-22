"""Tests for HTML generator."""
import json
from pathlib import Path

import pytest

from src.html_generator import generate_html, extract_latest_rates


@pytest.fixture
def sample_bnz_data(tmp_path):
    """Create sample BNZ data file."""
    data = {
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

    # Check Variable rate
    standard_var = next(r for r in latest if r["product_name"] == "Standard" and r["term"] == "Variable")
    assert standard_var["rate_percentage"] == 5.84


def test_extract_latest_rates_empty_file(tmp_path):
    """Test extracting from empty data file."""
    empty_data = {
        "last_scraped": None,
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


def test_generate_html_multiple_banks(tmp_path):
    """Test generating HTML with multiple banks."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create BNZ data
    bnz_data = {
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

    # Create ANZ data
    anz_data = {
        "last_scraped": "2025-12-22T12:00:00+13:00",
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
