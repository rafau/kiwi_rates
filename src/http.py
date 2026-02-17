"""Shared HTTP utilities."""
import time

import requests


def fetch_with_retry(url: str, headers: dict | None = None, max_retries: int = 5, backoff: float = 2.0, timeout: int = 60) -> requests.Response:
    """
    Fetch URL with retry logic and exponential backoff.

    Args:
        url: URL to fetch
        headers: Optional headers dictionary
        max_retries: Maximum number of retry attempts (default: 5)
        backoff: Initial backoff time in seconds (doubles each retry, default: 2.0)
        timeout: Request timeout in seconds (default: 60)

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            last_exception = e
            if attempt < max_retries - 1:
                sleep_time = backoff * (2 ** attempt)
                print(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {sleep_time}s...")
                time.sleep(sleep_time)

    raise last_exception
