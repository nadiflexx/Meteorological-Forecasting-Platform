from unittest.mock import MagicMock

from src.utils.resilience import fetch_with_retry_logic


def test_retry_success_first_try():
    mock_func = MagicMock(return_value=["data"])

    result = fetch_with_retry_logic(mock_func, max_retries=3, delay=0)

    assert result == ["data"]
    assert mock_func.call_count == 1


def test_retry_success_after_failure():
    mock_func = MagicMock(side_effect=[Exception("Fail"), ["data"]])

    result = fetch_with_retry_logic(mock_func, max_retries=3, delay=0)

    assert result == ["data"]
    assert mock_func.call_count == 2


def test_retry_all_fail():
    mock_func = MagicMock(side_effect=Exception("Fail forever"))

    result = fetch_with_retry_logic(mock_func, max_retries=3, delay=0)

    assert result == []
    assert mock_func.call_count == 3
