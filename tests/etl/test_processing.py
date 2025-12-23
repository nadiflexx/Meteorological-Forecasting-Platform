from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.etl.processing import WeatherProcessor


@pytest.fixture
def raw_df():
    return pd.DataFrame(
        {
            "fecha": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "indicativo": ["TEST"] * 3,
            "nombre": ["Station A"] * 3,
            "provincia": ["Barcelona"] * 3,
            "altitud": [10] * 3,
            "tmed": [15.0, np.nan, 16.0],
            "prec": [0.0, np.nan, 0.0],
        }
    )


@patch("src.etl.processing.OpenMeteoClient")
def test_processing_logic(mock_om_client, raw_df):
    mock_om_client.return_value.fetch_solar_data.return_value = pd.DataFrame()

    processor = WeatherProcessor()

    with (
        patch("src.etl.processing.STATIONS", {"TEST": "Station A"}),
        patch("src.etl.processing.STATION_COORDS", {"TEST": {"lat": 0, "lon": 0}}),
    ):
        result_df = processor.process_stations_logic(raw_df)

    assert not result_df.empty
    assert result_df.iloc[1]["tmed"] == 15.5
    assert result_df.iloc[1]["tmed_est"] == 1
