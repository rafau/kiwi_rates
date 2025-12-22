"""Generate HTML visualization from rate data."""
import json
from datetime import datetime
from pathlib import Path


def extract_latest_rates(data_file: Path) -> list[dict]:
    """
    Extract latest rates from a data file.

    Args:
        data_file: Path to bank rates JSON file

    Returns:
        List of latest rate entries per product/term combination
    """
    with open(data_file) as f:
        data = json.load(f)

    rates = data.get("rates", [])

    if not rates:
        return []

    # Build map of latest rate per product/term
    latest_map = {}
    for rate in rates:
        key = (rate["product_name"], rate["term"])
        # Keep the most recent (assuming chronological order, or compare scraped_at)
        if key not in latest_map:
            latest_map[key] = rate
        else:
            # Compare timestamps to keep the latest
            if rate["scraped_at"] > latest_map[key]["scraped_at"]:
                latest_map[key] = rate

    return list(latest_map.values())


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

                html += f"""                <tr>
                    <td>{rate['product_name']}</td>
                    <td>{rate['term']}</td>
                    <td class="rate">{rate['rate_percentage']:.2f}%</td>
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
