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

        # Get latest rate
        latest = sorted_rates[-1]

        # Calculate change
        if len(sorted_rates) >= 2:
            previous = sorted_rates[-2]
            rate_change = round(latest["rate_percentage"] - previous["rate_percentage"], 2)
        else:
            rate_change = 0.00

        # Determine if this is a recent change (within last 2 weeks)
        is_recent_change = False
        if rate_change != 0.00:
            # Parse scraped_at timestamp
            scraped_date = datetime.fromisoformat(latest["scraped_at"])
            now = datetime.now(scraped_date.tzinfo)  # Use same timezone
            days_since_change = (now - scraped_date).days
            is_recent_change = days_since_change <= 14

        # Add rate_change and is_recent_change fields to latest entry
        enriched_rate = latest.copy()
        enriched_rate["rate_change"] = rate_change
        enriched_rate["is_recent_change"] = is_recent_change
        result.append(enriched_rate)

    return result


def generate_html(data_dir: Path, output_file: Path) -> None:
    """
    Generate HTML visualization from all rate data files.

    Args:
        data_dir: Directory containing rate JSON files
        output_file: Path to output HTML file
    """
    # Collect all rate files
    rate_files = sorted(data_dir.glob("*_rates.json"))

    # Build data structure: bank -> rates
    bank_rates = {}

    for rate_file in rate_files:
        # Extract bank name from filename (e.g., "bnz_rates.json" -> "BNZ")
        bank_name = rate_file.stem.replace("_rates", "").upper()

        latest_rates = extract_latest_rates(rate_file)

        if latest_rates:
            bank_rates[bank_name] = sorted(
                latest_rates,
                key=lambda r: (r["product_name"], r["term"])
            )

    # Generate HTML
    html = generate_html_content(bank_rates)

    # Save to file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html)


def generate_html_content(bank_rates: dict[str, list[dict]]) -> str:
    """
    Generate HTML content from bank rates data.

    Args:
        bank_rates: Dictionary mapping bank name to list of rates

    Returns:
        HTML string
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
    </style>
</head>
<body>
    <h1>Kiwi Rates</h1>
    <p class="last-updated">Last updated: {now}</p>
"""

    if not bank_rates:
        html += """    <p style="text-align: center; color: #666;">No rate data available.</p>
"""
    else:
        for bank_name, rates in sorted(bank_rates.items()):
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
                # Format the scraped_at date
                try:
                    scraped_date = datetime.fromisoformat(rate["scraped_at"]).strftime("%Y-%m-%d")
                except:
                    scraped_date = rate["scraped_at"]

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

                html += f"""                <tr{row_class}>
                    <td>{rate['product_name']}</td>
                    <td>{rate['term']}</td>
                    <td class="rate">{rate['rate_percentage']:.2f}% <span class="{change_class}">({sign}{abs(rate_change):.2f})</span></td>
                    <td>{scraped_date}</td>
                </tr>
"""

            html += """            </tbody>
        </table>
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
