"""
Resilience Utilities.
Logic for retries, error handling, and fault tolerance.
"""

from collections.abc import Callable
import time
from typing import Any

from src.config.settings import APIs
from src.utils.logger import log


def fetch_with_retry_logic(
    fetch_func: Callable, max_retries: int = 3, delay: int = 2, *args, **kwargs
) -> list[Any]:
    """
    Executes a fetching function with custom retry logic.

    Trigger conditions for retry:
    1. Exception raised (Connection error, Timeout).
    2. Empty data returned (Specific requirement for AEMET).

    Args:
        fetch_func (Callable): The client method to execute.
        max_retries (int): Maximum attempts.
        delay (int): Base seconds to wait between retries (exponential backoff).
        *args, **kwargs: Arguments passed to fetch_func.

    Returns:
        List[Any]: The data retrieved or an empty list if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            # Execute the function passed as argument
            data = fetch_func(*args, **kwargs)

            if data:
                return data

            # Logic: If empty list, maybe transient issue. Retry.
            if attempt < max_retries - 1:
                wait_time = delay * (2**attempt)
                log.warning(
                    f"⚠️ Empty response. Retrying in {wait_time}s... (Attempt {attempt + 1})"
                )
                time.sleep(wait_time)

        except ConnectionError:
            # If we are here (429 or Exception), wait and retry loop
            log.info(f"⏳ Waiting {APIs.RETRY_DELAY}s to retry...")
            time.sleep(APIs.RETRY_DELAY)

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = delay * (2**attempt)
                log.error(f"❌ Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                log.error(f"❌ Failed after {max_retries} attempts: {e}")

    return []
