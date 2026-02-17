"""Tests for shared HTTP utilities."""
from unittest.mock import patch, MagicMock

import pytest
import requests

from src.http import fetch_with_retry


@patch("src.http.time.sleep")
@patch("src.http.requests.get")
def test_fetch_with_retry_success_first_attempt(mock_get, mock_sleep):
    """Test successful fetch on first attempt."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = fetch_with_retry("https://example.com")

    assert result is mock_response
    mock_get.assert_called_once()
    mock_sleep.assert_not_called()


@patch("src.http.time.sleep")
@patch("src.http.requests.get")
def test_fetch_with_retry_succeeds_after_failures(mock_get, mock_sleep):
    """Test successful fetch after transient failures."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_get.side_effect = [
        requests.ConnectionError("fail 1"),
        requests.ConnectionError("fail 2"),
        mock_response,
    ]

    result = fetch_with_retry("https://example.com", max_retries=5, backoff=1.0)

    assert result is mock_response
    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("src.http.time.sleep")
@patch("src.http.requests.get")
def test_fetch_with_retry_raises_after_all_retries(mock_get, mock_sleep):
    """Test raises last exception after exhausting all retries."""
    mock_get.side_effect = requests.ConnectionError("persistent failure")

    with pytest.raises(requests.ConnectionError, match="persistent failure"):
        fetch_with_retry("https://example.com", max_retries=3, backoff=1.0)

    assert mock_get.call_count == 3
    assert mock_sleep.call_count == 2


@patch("src.http.time.sleep")
@patch("src.http.requests.get")
def test_fetch_with_retry_exponential_backoff(mock_get, mock_sleep):
    """Test that backoff doubles each retry."""
    mock_get.side_effect = requests.ConnectionError("fail")

    with pytest.raises(requests.ConnectionError):
        fetch_with_retry("https://example.com", max_retries=4, backoff=2.0)

    # Backoff: 2*1=2, 2*2=4, 2*4=8 (no sleep after last attempt)
    assert mock_sleep.call_count == 3
    mock_sleep.assert_any_call(2.0)
    mock_sleep.assert_any_call(4.0)
    mock_sleep.assert_any_call(8.0)


@patch("src.http.time.sleep")
@patch("src.http.requests.get")
def test_fetch_with_retry_passes_headers_and_timeout(mock_get, mock_sleep):
    """Test that headers and timeout are forwarded to requests.get."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    headers = {"Authorization": "Bearer token"}
    fetch_with_retry("https://example.com", headers=headers, timeout=30)

    mock_get.assert_called_once_with("https://example.com", headers=headers, timeout=30)


@patch("src.http.time.sleep")
@patch("src.http.requests.get")
def test_fetch_with_retry_raises_on_http_error(mock_get, mock_sleep):
    """Test that HTTP errors (4xx, 5xx) trigger retries."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    mock_get.return_value = mock_response

    with pytest.raises(requests.HTTPError):
        fetch_with_retry("https://example.com", max_retries=2, backoff=1.0)

    assert mock_get.call_count == 2
