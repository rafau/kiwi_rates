"""Notification module for rate changes via ntfy.sh."""
import os

import requests


def get_ntfy_topic() -> str | None:
    """Read NTFY_TOPIC env var. Returns None if not set or empty."""
    topic = os.environ.get("NTFY_TOPIC", "")
    return topic if topic else None


def format_notification(bank_name: str, changed_rates: list[dict], existing_rates: list[dict]) -> tuple[str, str]:
    """
    Format a notification message for rate changes.

    Returns:
        Tuple of (title, body) for the notification.
    """
    # Build lookup of previous rates: {(product_name, term): rate_percentage}
    latest_existing = {}
    for rate in existing_rates:
        key = (rate["product_name"], rate["term"])
        latest_existing[key] = rate["rate_percentage"]

    # Title
    count = len(changed_rates)
    title = f"{bank_name}: {count} rate{'s' if count != 1 else ''} changed"

    # Body — one markdown list item per changed rate
    lines = []
    for rate in changed_rates:
        key = (rate["product_name"], rate["term"])
        old_rate = latest_existing.get(key)
        if old_rate is not None:
            lines.append(f"- {rate['product_name']} {rate['term']}: {old_rate}% -> {rate['rate_percentage']}%")
        else:
            lines.append(f"- {rate['product_name']} {rate['term']}: {rate['rate_percentage']}% (new)")

    body = "\n".join(lines)
    return title, body


def send_notification(topic: str, title: str, body: str, tags: str = "chart_with_upwards_trend") -> bool:
    """Send notification via ntfy.sh. Never raises."""
    try:
        response = requests.post(
            f"https://ntfy.sh/{topic}",
            data=body.encode("utf-8"),
            headers={
                "Title": title,
                "Tags": tags,
                "Markdown": "yes",
            },
            timeout=10,
        )
        response.raise_for_status()
        print(f"  Notification sent to ntfy.sh/{topic}")
        return True
    except Exception as e:
        print(f"  Warning: Failed to send notification: {e}")
        return False


def notify_rate_changes(bank_name: str, changed_rates: list[dict], existing_rates: list[dict]) -> None:
    """
    Main entry point. Checks topic, formats message, sends notification.

    Silent no-op if topic not configured. Never raises.
    """
    topic = get_ntfy_topic()
    if topic is None:
        return

    try:
        title, body = format_notification(bank_name, changed_rates, existing_rates)
        send_notification(topic, title, body)
    except Exception as e:
        print(f"  Warning: Notification failed: {e}")
