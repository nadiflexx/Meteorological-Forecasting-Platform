from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np

from src.etl.clients.openmeteo import OpenMeteoClient


@patch("src.etl.clients.openmeteo.openmeteo_requests.Client")
def test_openmeteo_fetch_success(mock_client_cls):
    mock_instance = mock_client_cls.return_value
    mock_response = MagicMock()
    mock_daily = MagicMock()

    mock_daily.Variables.side_effect = [
        MagicMock(ValuesAsNumpy=lambda: np.array([3600.0, 7200.0])),
        MagicMock(ValuesAsNumpy=lambda: np.array([0.0, 5.0])),
        MagicMock(ValuesAsNumpy=lambda: np.array([1013.0, 1010.0])),
        MagicMock(ValuesAsNumpy=lambda: np.array([10.0, 80.0])),
    ]

    mock_daily.Time.return_value = 1672531200
    mock_daily.TimeEnd.return_value = 1672704000
    mock_daily.Interval.return_value = 86400

    mock_response.Daily.return_value = mock_daily
    mock_instance.weather_api.return_value = [mock_response]

    client = OpenMeteoClient()

    df = client.fetch_solar_data(
        lat=41.0,
        lon=2.0,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 2),
    )

    assert not df.empty
    assert "sol" in df.columns
    assert df.iloc[0]["sol"] == 1.0
