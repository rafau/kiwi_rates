"""Tests for ntfy.sh notification module."""
from unittest.mock import patch, MagicMock

import pytest
import requests

from src.notifier import get_ntfy_topic, format_notification, send_notification, notify_rate_changes


# --- get_ntfy_topic ---

def test_get_ntfy_topic_returns_topic_when_set(monkeypatch):
    """Test returns topic value when NTFY_TOPIC is set."""
    monkeypatch.setenv("NTFY_TOPIC", "my-kiwi-rates")
    assert get_ntfy_topic() == "my-kiwi-rates"


def test_get_ntfy_topic_returns_none_when_unset(monkeypatch):
    """Test returns None when NTFY_TOPIC is not set."""
    monkeypatch.delenv("NTFY_TOPIC", raising=False)
    assert get_ntfy_topic() is None


def test_get_ntfy_topic_returns_none_when_empty(monkeypatch):
    """Test returns None when NTFY_TOPIC is empty string."""
    monkeypatch.setenv("NTFY_TOPIC", "")
    assert get_ntfy_topic() is None


# --- format_notification ---

def test_format_notification_single_change():
    """Test formatting with a single rate change."""
    changed_rates = [
        {"product_name": "Standard", "term": "1 year", "rate_percentage": 4.29}
    ]
    existing_rates = [
        {"product_name": "Standard", "term": "1 year", "rate_percentage": 4.49}
    ]

    title, body = format_notification("BNZ", changed_rates, existing_rates)

    assert title == "BNZ: 1 rate changed"
    assert "Standard 1 year: 4.49% -> 4.29%" in body


def test_format_notification_multiple_changes():
    """Test formatting with multiple rate changes."""
    changed_rates = [
        {"product_name": "Standard", "term": "1 year", "rate_percentage": 4.29},
        {"product_name": "Standard", "term": "2 years", "rate_percentage": 4.79},
    ]
    existing_rates = [
        {"product_name": "Standard", "term": "1 year", "rate_percentage": 4.49},
        {"product_name": "Standard", "term": "2 years", "rate_percentage": 4.69},
    ]

    title, body = format_notification("BNZ", changed_rates, existing_rates)

    assert title == "BNZ: 2 rates changed"
    assert "Standard 1 year: 4.49% -> 4.29%" in body
    assert "Standard 2 years: 4.69% -> 4.79%" in body


def test_format_notification_new_product():
    """Test formatting when a product is new (not in existing rates)."""
    changed_rates = [
        {"product_name": "TotalMoney", "term": "Variable", "rate_percentage": 5.84}
    ]
    existing_rates = [
        {"product_name": "Standard", "term": "1 year", "rate_percentage": 4.49}
    ]

    title, body = format_notification("BNZ", changed_rates, existing_rates)

    assert title == "BNZ: 1 rate changed"
    assert "TotalMoney Variable: 5.84% (new)" in body


def test_format_notification_mixed_changes_and_new():
    """Test formatting with both changed and new rates."""
    changed_rates = [
        {"product_name": "Standard", "term": "1 year", "rate_percentage": 4.29},
        {"product_name": "TotalMoney", "term": "Variable", "rate_percentage": 5.84},
    ]
    existing_rates = [
        {"product_name": "Standard", "term": "1 year", "rate_percentage": 4.49},
    ]

    title, body = format_notification("BNZ", changed_rates, existing_rates)

    assert title == "BNZ: 2 rates changed"
    assert "Standard 1 year: 4.49% -> 4.29%" in body
    assert "TotalMoney Variable: 5.84% (new)" in body


# --- send_notification ---

@patch("src.notifier.requests.post")
def test_send_notification_success(mock_post):
    """Test successful notification returns True."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = send_notification("test-topic", "Title", "Body text")

    assert result is True
    mock_post.assert_called_once_with(
        "https://ntfy.sh/test-topic",
        data="Body text".encode("utf-8"),
        headers={
            "Title": "Title",
            "Tags": "chart_with_upwards_trend",
            "Markdown": "yes",
        },
        timeout=10,
    )


@patch("src.notifier.requests.post")
def test_send_notification_network_error(mock_post):
    """Test network error returns False and doesn't raise."""
    mock_post.side_effect = requests.ConnectionError("Network unreachable")

    result = send_notification("test-topic", "Title", "Body")

    assert result is False


@patch("src.notifier.requests.post")
def test_send_notification_http_error(mock_post):
    """Test HTTP 500 error returns False and doesn't raise."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    mock_post.return_value = mock_response

    result = send_notification("test-topic", "Title", "Body")

    assert result is False


# --- notify_rate_changes ---

@patch("src.notifier.send_notification")
@patch("src.notifier.get_ntfy_topic")
def test_notify_rate_changes_sends_when_configured(mock_get_topic, mock_send):
    """Test sends notification when topic is configured."""
    mock_get_topic.return_value = "my-topic"
    mock_send.return_value = True

    notify_rate_changes(
        bank_name="BNZ",
        changed_rates=[{"product_name": "Standard", "term": "1 year", "rate_percentage": 4.29}],
        existing_rates=[{"product_name": "Standard", "term": "1 year", "rate_percentage": 4.49}],
    )

    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == "my-topic"
    assert "BNZ" in call_args[0][1]


@patch("src.notifier.send_notification")
@patch("src.notifier.get_ntfy_topic")
def test_notify_rate_changes_skips_when_not_configured(mock_get_topic, mock_send):
    """Test skips notification when topic is not configured."""
    mock_get_topic.return_value = None

    notify_rate_changes(
        bank_name="BNZ",
        changed_rates=[{"product_name": "Standard", "term": "1 year", "rate_percentage": 4.29}],
        existing_rates=[],
    )

    mock_send.assert_not_called()


@patch("src.notifier.send_notification")
@patch("src.notifier.get_ntfy_topic")
def test_notify_rate_changes_never_raises_on_failure(mock_get_topic, mock_send):
    """Test never raises even when send_notification fails."""
    mock_get_topic.return_value = "my-topic"
    mock_send.side_effect = Exception("Unexpected error")

    # Should not raise
    notify_rate_changes(
        bank_name="BNZ",
        changed_rates=[{"product_name": "Standard", "term": "1 year", "rate_percentage": 4.29}],
        existing_rates=[],
    )
