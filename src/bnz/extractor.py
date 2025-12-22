"""Extract BNZ API key from HTML pages."""
import re


def extract_api_key(html_content: str) -> str:
    """
    Extract BNZ API key from HTML page.

    Looks for window.__bootstrap object and extracts the apiKey value.

    Args:
        html_content: HTML string from BNZ website

    Returns:
        API key string

    Raises:
        ValueError: If API key not found in HTML
    """
    # Pattern to match: apiKey: 'value' or apiKey: "value" or apiKey:'value'
    pattern = r'apiKey\s*:\s*["\']([^"\']+)["\']'

    match = re.search(pattern, html_content)

    if not match:
        raise ValueError("API key not found in HTML")

    return match.group(1)
