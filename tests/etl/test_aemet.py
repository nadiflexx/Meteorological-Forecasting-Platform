import contextlib
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.etl.clients.aemet import AemetClient


@patch("src.etl.clients.aemet.requests.Session")
def test_aemet_fetch_success(mock_session_cls):
    mock_session = mock_session_cls.return_value

    mock_res_1 = MagicMock()
    mock_res_1.status_code = 200
    mock_res_1.json.return_value = {"estado": 200, "datos": "http://download.url"}

    mock_res_2 = MagicMock()
    mock_res_2.status_code = 200
    mock_res_2.json.return_value = [{"fecha": "2024-01-01", "valor": 10}]

    mock_session.get.side_effect = [mock_res_1, mock_res_2]

    client = AemetClient()
    data = client.fetch_data_chunk(datetime(2024, 1, 1), datetime(2024, 1, 2), "TEST")

    assert data is not None
    assert len(data) == 1
    assert data[0]["valor"] == 10


@patch("src.etl.clients.aemet.requests.Session")
def test_aemet_rate_limit(mock_session_cls):
    mock_session = mock_session_cls.return_value

    mock_res = MagicMock()
    mock_res.status_code = 429

    mock_session.get.side_effect = [mock_res, Exception("Break Loop")]

    client = AemetClient()

    with contextlib.suppress(ConnectionError):
        client.fetch_data_chunk(datetime(2024, 1, 1), datetime(2024, 1, 2), "TEST")

    assert mock_session.get.called
