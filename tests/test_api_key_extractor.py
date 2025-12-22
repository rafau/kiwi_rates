"""Tests for API key extraction from HTML."""
from pathlib import Path

import pytest

from src.bnz.extractor import extract_api_key


@pytest.fixture
def bnz_html():
    """Load BNZ HTML fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "bnz_page.html"
    return fixture_path.read_text()


def test_extract_bnz_api_key(bnz_html):
    """Test extracting BNZ API key from HTML."""
    api_key = extract_api_key(bnz_html)

    assert api_key == "vjqaLG3y07VHpZnIe8nYX808FGPYid8G"


def test_extract_bnz_api_key_different_format():
    """Test extracting API key with different whitespace."""
    html = """
    <script>
    window.__bootstrap={apiKey:'testkey123',other:'value'}
    </script>
    """

    api_key = extract_api_key(html)
    assert api_key == "testkey123"


def test_extract_bnz_api_key_multiline():
    """Test extracting API key from multiline script."""
    html = """
    <script>
    window.__bootstrap = {
        env: 'test',
        apiKey: 'multilinekey456',
        other: 'data'
    };
    </script>
    """

    api_key = extract_api_key(html)
    assert api_key == "multilinekey456"


def test_extract_bnz_api_key_not_found():
    """Test error when API key not found."""
    html = "<html><body>No API key here</body></html>"

    with pytest.raises(ValueError, match="API key not found"):
        extract_api_key(html)


def test_extract_bnz_api_key_double_quotes():
    """Test extracting API key with double quotes."""
    html = '''
    <script>
    window.__bootstrap = {
        apiKey: "doublequoted789"
    };
    </script>
    '''

    api_key = extract_api_key(html)
    assert api_key == "doublequoted789"
