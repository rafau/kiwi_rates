"""Tests for BNZ rate parser."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.bnz.parser import parse_rates, parse_last_updated


@pytest.fixture
def bnz_xml():
    """Load BNZ XML fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "bnz_rates.xml"
    return fixture_path.read_text()


def test_parse_bnz_last_updated(bnz_xml):
    """Test parsing BNZ last updated date."""
    result = parse_last_updated(bnz_xml)

    expected = datetime(2025, 12, 18, 0, 0, 0, tzinfo=ZoneInfo("Pacific/Auckland"))
    assert result == expected


def test_parse_bnz_last_updated_format():
    """Test parsing different BNZ date format."""
    xml = """<?xml version="1.0"?>
    <rss><standard><lastupdated>Monday, 1 January 2024</lastupdated></standard></rss>"""

    result = parse_last_updated(xml)
    expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("Pacific/Auckland"))
    assert result == expected


def test_parse_bnz_rates(bnz_xml):
    """Test parsing BNZ rates from XML."""
    rates = parse_rates(bnz_xml)

    # Should have 12 rates in the fixture
    assert len(rates) == 12

    # Check first rate (TotalMoney Variable)
    assert rates[0] == {
        "product_name": "TotalMoney",
        "term": "Variable",
        "rate_percentage": 5.94
    }

    # Check a fixed rate (Standard 1 year)
    standard_1y = next(r for r in rates if r["product_name"] == "Standard" and r["term"] == "1 year")
    assert standard_1y == {
        "product_name": "Standard",
        "term": "1 year",
        "rate_percentage": 4.49
    }


def test_parse_bnz_rates_strips_whitespace():
    """Test that parser strips whitespace from labels."""
    xml = """<?xml version="1.0"?>
    <rss><standard>
        <rate><label>  Spaced Label  </label><term>Variable</term><interest>5.5</interest></rate>
    </standard></rss>"""

    rates = parse_rates(xml)
    assert rates[0]["product_name"] == "Spaced Label"


def test_parse_bnz_rates_empty():
    """Test parsing XML with no rates."""
    xml = """<?xml version="1.0"?><rss><standard></standard></rss>"""

    rates = parse_rates(xml)
    assert rates == []


def test_parse_bnz_rates_converts_interest_to_float():
    """Test that interest rates are converted to float."""
    xml = """<?xml version="1.0"?>
    <rss><standard>
        <rate><label>Test</label><term>1 year</term><interest>4.69</interest></rate>
    </standard></rss>"""

    rates = parse_rates(xml)
    assert isinstance(rates[0]["rate_percentage"], float)
    assert rates[0]["rate_percentage"] == 4.69
