import numpy as np
import pandas as pd

from src.features.transformation import FeatureEngineer


def test_add_wind_components():
    df = pd.DataFrame({"dir": [0, 90, 180, 270]})
    df = FeatureEngineer.add_wind_components(df)

    assert np.isclose(df.iloc[1]["wind_sin"], 1.0)
    assert np.isclose(df.iloc[1]["wind_cos"], 0.0, atol=1e-10)


def test_create_lags():
    df = pd.DataFrame({"val": [1, 2, 3], "indicativo": ["A", "A", "A"]})
    df = FeatureEngineer.create_lags(df, ["val"], [1], "indicativo")

    assert np.isnan(df.iloc[0]["val_lag_1"])
    assert df.iloc[1]["val_lag_1"] == 1.0
