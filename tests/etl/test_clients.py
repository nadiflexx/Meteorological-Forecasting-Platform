from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np

from src.etl.clients.openmeteo import OpenMeteoClient


@patch("src.etl.clients.openmeteo.openmeteo_requests.Client")
def test_openmeteo_fetch_success(mock_client_cls):
    # 1. Preparar Mock
    mock_instance = mock_client_cls.return_value
    mock_response = MagicMock()
    mock_daily = MagicMock()

    # IMPORTANTE: Simular datos válidos
    mock_daily.Variables.side_effect = [
        MagicMock(ValuesAsNumpy=lambda: np.array([3600.0, 7200.0])),  # Sol
        MagicMock(ValuesAsNumpy=lambda: np.array([0.0, 5.0])),  # Prec
        MagicMock(ValuesAsNumpy=lambda: np.array([1013.0, 1010.0])),  # Presion
        MagicMock(ValuesAsNumpy=lambda: np.array([10.0, 80.0])),  # Nubes
    ]

    # Fechas simuladas (Unix)
    mock_daily.Time.return_value = 1672531200  # 2023-01-01
    mock_daily.TimeEnd.return_value = 1672704000  # 2023-01-03
    mock_daily.Interval.return_value = 86400

    mock_response.Daily.return_value = mock_daily
    mock_instance.weather_api.return_value = [mock_response]

    client = OpenMeteoClient()

    # 2. Ejecutar con fecha PASADA (2023) para evitar bloqueo de "futuro"
    df = client.fetch_solar_data(
        lat=41.0,
        lon=2.0,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 2),
    )

    # 3. Validar
    assert not df.empty
    assert "sol" in df.columns
    assert df.iloc[0]["sol"] == 1.0
