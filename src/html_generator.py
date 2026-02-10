"""Generate HTML visualization from rate data."""
import json
from datetime import datetime, timedelta
from pathlib import Path


def extract_latest_rates(data_file: Path) -> list[dict]:
    """
    Extract latest rates with change calculation from data file.

    Args:
        data_file: Path to bank rates JSON file

    Returns:
        List of latest rate entries per product/term combination,
        each enriched with a 'rate_change' field
    """
    with open(data_file) as f:
        data = json.load(f)

    rates = data.get("rates", [])

    if not rates:
        return []

    # Build map tracking ALL rates per product/term (not just latest)
    rates_by_product = {}  # key: (product_name, term) -> list of rate entries

    for rate in rates:
        key = (rate["product_name"], rate["term"])
        if key not in rates_by_product:
            rates_by_product[key] = []
        rates_by_product[key].append(rate)

    # Extract latest and calculate changes
    result = []
    for key, rate_list in rates_by_product.items():
        # Sort by scraped_at to ensure chronological order
        sorted_rates = sorted(rate_list, key=lambda r: r["scraped_at"])

        # Find when this product first appeared
        min_scraped_date = min(datetime.fromisoformat(r["scraped_at"]) for r in sorted_rates)

        # Calculate days since first appearance
        now = datetime.now(min_scraped_date.tzinfo)  # Use same timezone
        days_since_first_appearance = (now - min_scraped_date).days

        # Mark as new if first appeared within 30 days (boundary: 30 days = NOT new)
        is_new_product = days_since_first_appearance < 30

        # Get latest rate
        latest = sorted_rates[-1]

        # Calculate change
        if len(sorted_rates) >= 2:
            previous = sorted_rates[-2]
            rate_change = round(latest["rate_percentage"] - previous["rate_percentage"], 2)
        else:
            rate_change = 0.00

        # Calculate days since last update (always, for all rates)
        scraped_date = datetime.fromisoformat(latest["scraped_at"])
        now = datetime.now(scraped_date.tzinfo)
        days_since_update = (now - scraped_date).days

        # Determine if this is a recent change (within last 2 weeks)
        is_recent_change = False
        if rate_change != 0.00:
            is_recent_change = days_since_update <= 14

        # Add rate_change and is_recent_change fields to latest entry
        enriched_rate = latest.copy()
        enriched_rate["rate_change"] = rate_change
        enriched_rate["is_recent_change"] = is_recent_change
        enriched_rate["is_new_product"] = is_new_product
        enriched_rate["days_since_first_appearance"] = days_since_first_appearance
        enriched_rate["days_since_update"] = days_since_update
        result.append(enriched_rate)

    return result


def get_most_recent_rate_change(rates: list[dict]) -> tuple[str, int] | None:
    """
    Find most recent rate change date from a list of rates.

    Args:
        rates: List of rate entries (with rate_change field)

    Returns:
        Tuple of (formatted date string YYYY-MM-DD, days since change) or None if no changes detected
    """
    if not rates:
        return None

    # Filter to only rates with actual changes
    changed_rates = [r for r in rates if r.get("rate_change", 0.00) != 0.00]

    if not changed_rates:
        return None

    # Find the most recent scraped_at date
    most_recent = max(changed_rates, key=lambda r: r["scraped_at"])

    # Format as YYYY-MM-DD
    # Let this raise ValueError if date is malformed - FAIL LOUDLY
    scraped_date = datetime.fromisoformat(most_recent["scraped_at"])
    days_since = (datetime.now(scraped_date.tzinfo) - scraped_date).days
    return (scraped_date.strftime("%Y-%m-%d"), days_since)


def generate_html(data_dir: Path, output_file: Path) -> None:
    """
    Generate HTML visualization from all rate data files.

    Args:
        data_dir: Directory containing rate JSON files
        output_file: Path to output HTML file
    """
    # Collect all rate files
    rate_files = sorted(data_dir.glob("*_rates.json"))

    # Build data structure: bank -> {rates, last_scraped}
    bank_data = {}
    all_rates = []  # Collect all rates to find global most recent change

    for rate_file in rate_files:
        # Extract bank name from filename (e.g., "bnz_rates.json" -> "BNZ")
        bank_name = rate_file.stem.replace("_rates", "").upper()

        # Load full JSON to get metadata
        with open(rate_file) as f:
            data = json.load(f)

        latest_rates = extract_latest_rates(rate_file)

        if latest_rates:
            bank_data[bank_name] = {
                "rates": sorted(latest_rates, key=lambda r: (r["product_name"], r["term"]))
            }
            all_rates.extend(latest_rates)

    # Calculate most recent rate change across all banks
    most_recent_change = get_most_recent_rate_change(all_rates)

    # Generate HTML
    html = generate_html_content(bank_data, most_recent_change)

    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html)


def generate_html_content(bank_data: dict[str, dict], most_recent_change: tuple[str, int] | None) -> str:
    """
    Generate HTML content from bank rates data.

    Args:
        bank_data: Dictionary mapping bank name to dict with 'rates'
        most_recent_change: Tuple of (date string YYYY-MM-DD, days since change) or None

    Returns:
        HTML string
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format last rate change display
    if most_recent_change:
        date_str, days_since = most_recent_change
        last_change_display = f'Last rate change: {date_str} <span class="days-ago">({days_since}d)</span>'
    else:
        last_change_display = "Last rate change: No changes detected"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kiwi Rates - NZ Home Loan Rates</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .last-updated {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .bank-section {{
            background: white;
            margin-bottom: 30px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #2c5282;
            margin-top: 0;
            border-bottom: 2px solid #2c5282;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background-color: #2c5282;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{
            background-color: #f7fafc;
        }}
        .rate {{
            font-weight: 600;
            color: #2c5282;
        }}
        .rate-change-positive {{
            color: #e53e3e;
            font-size: 0.9em;
            margin-left: 4px;
        }}
        .rate-change-negative {{
            color: #38a169;
            font-size: 0.9em;
            margin-left: 4px;
        }}
        .rate-change-neutral {{
            color: #718096;
            font-size: 0.9em;
            margin-left: 4px;
        }}
        .recent-change {{
            background-color: #fff3cd;
            font-weight: 500;
        }}
        .recent-change:hover {{
            background-color: #ffe69c;
        }}
        .new-product-badge {{
            display: inline-block;
            background-color: #bee3f8;  /* Light blue */
            color: #2c5282;             /* Dark blue (matches existing theme) */
            font-size: 0.75em;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .days-ago {{
            color: #718096;
            font-size: 0.85em;
        }}
        .bank-dates {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e2e8f0;
            font-size: 0.85em;
            color: #718096;
            text-align: left;
        }}
        .bank-dates p {{
            margin: 3px 0;
        }}

        /* Mobile responsive styles */
        @media (max-width: 768px) {{
            /* Reduce body padding on mobile */
            body {{
                padding: 10px;
            }}

            /* Adjust bank section spacing */
            .bank-section {{
                padding: 15px;
                margin-bottom: 20px;
            }}

            /* Hide table header on mobile */
            table thead {{
                display: none;
            }}

            /* Convert table to block layout */
            table, tbody, tr, td {{
                display: block;
                width: 100%;
            }}

            /* Style rows as cards */
            tr {{
                margin-bottom: 15px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
            }}

            /* Maintain recent-change highlighting */
            tr.recent-change {{
                background-color: #fff3cd;
                border-color: #ffc107;
            }}

            tr.recent-change:hover {{
                background-color: #ffe69c;
            }}

            /* Cell spacing */
            td {{
                padding: 8px 0;
                border-bottom: none;
                text-align: left;
            }}

            /* Product name styling (first cell) */
            td:first-child {{
                font-size: 1.1em;
                font-weight: 600;
                color: #2c5282;
                padding-bottom: 10px;
                border-bottom: 1px solid #e2e8f0;
                margin-bottom: 8px;
            }}

            /* Add labels using CSS pseudo-elements */
            td:nth-child(2)::before {{
                content: "Term: ";
                font-weight: 600;
                color: #4a5568;
            }}

            td:nth-child(3)::before {{
                content: "Rate: ";
                font-weight: 600;
                color: #4a5568;
            }}

            td:nth-child(4)::before {{
                content: "Last Updated: ";
                font-weight: 600;
                color: #4a5568;
            }}

            /* Rate cell emphasis */
            td:nth-child(3) {{
                font-size: 1.15em;
            }}

            /* Last updated cell styling */
            td:nth-child(4) {{
                color: #718096;
                font-size: 0.9em;
            }}

            /* Remove desktop hover effect */
            tr:hover {{
                background-color: inherit;
            }}

            /* Adjust rate change indicator size */
            .rate-change-positive,
            .rate-change-negative,
            .rate-change-neutral {{
                font-size: 0.85em;
            }}

            /* Adjust NEW badge size */
            .new-product-badge {{
                font-size: 0.7em;
            }}

            /* Responsive typography */
            h1 {{
                font-size: 1.5em;
            }}

            h2 {{
                font-size: 1.3em;
            }}

            .last-updated {{
                font-size: 0.9em;
            }}

            /* Bank dates responsive styling */
            .bank-dates {{
                font-size: 0.85em;
            }}
        }}

        /* Optional: Tablet optimization */
        @media (max-width: 1024px) and (min-width: 769px) {{
            body {{
                padding: 15px;
            }}

            th, td {{
                padding: 10px;
                font-size: 0.95em;
            }}
        }}
    </style>
</head>
<body>
    <h1>Kiwi Rates</h1>
    <p class="last-updated">{last_change_display}</p>
"""

    if not bank_data:
        html += """    <p style="text-align: center; color: #666;">No rate data available.</p>
"""
    else:
        for bank_name, bank_info in sorted(bank_data.items()):
            rates = bank_info["rates"]

            html += f"""
    <div class="bank-section">
        <h2>{bank_name}</h2>
        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Term</th>
                    <th>Rate</th>
                    <th>Last Updated</th>
                </tr>
            </thead>
            <tbody>
"""

            for rate in rates:
                # Format the scraped_at date - let it raise ValueError if malformed (FAIL LOUDLY)
                scraped_date = datetime.fromisoformat(rate["scraped_at"]).strftime("%Y-%m-%d")

                # Determine change styling
                rate_change = rate.get("rate_change", 0.00)
                if rate_change > 0:
                    change_class = "rate-change-positive"
                    sign = "+"
                elif rate_change < 0:
                    change_class = "rate-change-negative"
                    sign = "-"
                else:
                    change_class = "rate-change-neutral"
                    sign = ""

                # Add recent-change class if applicable
                row_class = ' class="recent-change"' if rate.get("is_recent_change", False) else ""

                # Build product name with NEW badge if applicable
                product_display = rate['product_name']
                if rate.get('is_new_product', False):
                    product_display += ' <span class="new-product-badge">New</span>'

                html += f"""                <tr{row_class}>
                    <td>{product_display}</td>
                    <td>{rate['term']}</td>
                    <td class="rate">{rate['rate_percentage']:.2f}% <span class="{change_class}">({sign}{abs(rate_change):.2f})</span></td>
                    <td>{scraped_date} <span class="days-ago">({rate.get("days_since_update", "")}d)</span></td>
                </tr>
"""

            html += f"""            </tbody>
        </table>
        <div class="bank-dates">
            <p>Page generated: {now}</p>
        </div>
    </div>
"""

    html += """</body>
</html>
"""

    return html


def main():
    """Main entry point for HTML generator."""
    data_dir = Path(__file__).parent.parent / "data"
    output_file = Path(__file__).parent.parent / "docs" / "index.html"

    print("Generating HTML visualization...")

    try:
        generate_html(data_dir, output_file)
        print(f"✓ HTML generated successfully: {output_file}")
    except Exception as e:
        print(f"✗ HTML generation failed: {e}")
        raise


if __name__ == "__main__":
    main()
