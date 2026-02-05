"""BNZ rate feed XML parser."""
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo


def parse_last_updated(xml_content: str) -> datetime:
    """
    Parse BNZ last updated date from XML feed.

    Args:
        xml_content: XML string from BNZ API

    Returns:
        Datetime with Pacific/Auckland timezone
    """
    root = ET.fromstring(xml_content)
    lastupdated_elem = root.find(".//lastupdated")

    if lastupdated_elem is None or lastupdated_elem.text is None:
        raise ValueError("No lastupdated element found in XML")

    # Parse format: "Thursday, 18 December 2025"
    date_str = lastupdated_elem.text.strip()
    # Remove day name (e.g., "Thursday, ")
    date_parts = date_str.split(", ", 1)
    if len(date_parts) == 2:
        date_str = date_parts[1]

    # Parse the date
    dt = datetime.strptime(date_str, "%d %B %Y")

    # Add Pacific/Auckland timezone
    return dt.replace(tzinfo=ZoneInfo("Pacific/Auckland"))


def parse_rates(xml_content: str) -> list[dict[str, str | float]]:
    """
    Parse BNZ rates from XML feed.

    Args:
        xml_content: XML string from BNZ API

    Returns:
        List of rate dictionaries with product_name, term, and rate_percentage

    Raises:
        ValueError: If no rates found in XML feed
    """
    root = ET.fromstring(xml_content)
    rates = []

    for rate_elem in root.findall(".//rate"):
        label_elem = rate_elem.find("label")
        term_elem = rate_elem.find("term")
        interest_elem = rate_elem.find("interest")

        if label_elem is not None and term_elem is not None and interest_elem is not None:
            if label_elem.text and term_elem.text and interest_elem.text:
                rates.append({
                    "product_name": label_elem.text.strip(),
                    "term": term_elem.text.strip(),
                    "rate_percentage": float(interest_elem.text.strip())
                })

    if len(rates) == 0:
        raise ValueError("No rates found in XML feed - BNZ API may be down or response format changed")

    return rates
