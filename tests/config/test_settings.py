import pandas as pd
import pytest


@pytest.fixture
def sample_weather_df():
    """Generates a sample weather DataFrame for testing purposes."""
    return pd.DataFrame(
        {
            "fecha": pd.date_range(start="2024-01-01", periods=5),
            "indicativo": ["TEST01"] * 5,
            "prob_rain": [0.1, 0.8, 0.4, 0.95, 0.0],
            "pred_sol": [12.0, 5.0, 0.0, 6.0, 10.0],
            "pred_hrMedia": [40, 90, 95, 85, 30],
            "tmed": [15, 12, 10, 11, 20],
            "punto_rocio": [5, 10, 9, 9, 2],
        }
    )
