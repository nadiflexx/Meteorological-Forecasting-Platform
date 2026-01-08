from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.modeling.trainers.atmosphere import AtmosphereModel
from src.modeling.trainers.rain import RainClassifier
from src.modeling.trainers.temperature import TemperatureModel


@pytest.fixture
def training_data():
    dates = pd.date_range("2022-12-25", periods=20)
    df = pd.DataFrame(
        {
            "fecha": dates,
            "indicativo": ["TEST"] * 20,
            "nombre": ["A"] * 20,
            "provincia": ["B"] * 20,
            "prec": [0.0] * 20,
            "presion": [1013] * 20,
            "hrMedia": [80] * 20,
            "nubes": [50] * 20,
            "velmedia": [10] * 20,
            "sol": [5] * 20,
            "tmed": [15] * 20,
            "tmin": [10] * 20,
            "tmax": [20] * 20,
            "dir": [90] * 20,
        }
    )
    # IMPORTANT: load_and_prepare está mockeado en los tests, así que station_id no se crea.
    df["station_id"] = 0
    return df


def mock_predict(X, *args, **kwargs):
    return np.array([0.5] * len(X))


# --- Helpers: evitamos que el feature engineering meta NaNs masivos (lags/rolling) ---
def _no_op(df, *args, **kwargs):
    return df


# --- Parches comunes: split dates dentro del rango del fixture + lags/windows pequeños ---
COMMON_PATCHES = [
    patch(
        "src.config.settings.ExperimentConfig.VAL_START_DATE",
        pd.Timestamp("2022-12-31"),
    ),
    patch(
        "src.config.settings.ExperimentConfig.TEST_START_DATE",
        pd.Timestamp("2023-01-05"),
    ),
    patch("src.config.settings.FeatureConfig.LAGS", [1, 2]),
    patch("src.config.settings.FeatureConfig.WINDOWS", [2]),
    patch(
        "src.features.transformation.FeatureEngineer.create_lags", side_effect=_no_op
    ),
    patch(
        "src.features.transformation.FeatureEngineer.create_rolling_stats",
        side_effect=_no_op,
    ),
    patch(
        "src.features.transformation.FeatureEngineer.add_time_cyclicality",
        side_effect=_no_op,
    ),
    patch(
        "src.features.transformation.FeatureEngineer.add_wind_components",
        side_effect=_no_op,
    ),
]


@patch("src.modeling.base.lgb.train")
@patch("src.modeling.base.joblib.dump")
def test_rain_classifier_flow(mock_dump, mock_lgb_train, training_data):
    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_predict
    mock_lgb_train.return_value = mock_model

    trainer = RainClassifier("fake.csv")
    trainer.df = training_data

    with (
        COMMON_PATCHES[0],
        COMMON_PATCHES[1],
        COMMON_PATCHES[2],
        COMMON_PATCHES[3],
        COMMON_PATCHES[4],
        COMMON_PATCHES[5],
        COMMON_PATCHES[6],
        COMMON_PATCHES[7],
        patch.object(RainClassifier, "load_and_prepare", return_value=None),
    ):
        results = trainer.run_training()

    assert mock_lgb_train.called
    assert "prob_rain" in results.columns
    assert "is_raining" in results.columns


@patch("src.modeling.base.lgb.train")
@patch("src.modeling.base.joblib.dump")
def test_atmosphere_regressor_flow(mock_dump, mock_lgb_train, training_data):
    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_predict
    mock_lgb_train.return_value = mock_model

    trainer = AtmosphereModel("fake.csv")
    trainer.df = training_data

    with (
        COMMON_PATCHES[0],
        COMMON_PATCHES[1],
        COMMON_PATCHES[2],
        COMMON_PATCHES[3],
        COMMON_PATCHES[4],
        COMMON_PATCHES[5],
        COMMON_PATCHES[6],
        COMMON_PATCHES[7],
        patch.object(AtmosphereModel, "load_and_prepare", return_value=None),
    ):
        results = trainer.run_training()

    assert "pred_sol" in results.columns
    assert "pred_hrMedia" in results.columns
    assert "pred_velmedia" in results.columns


@patch("src.modeling.base.lgb.train")
@patch("src.modeling.base.joblib.dump")
def test_temperature_regressor_flow(mock_dump, mock_lgb_train, training_data):
    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_predict
    mock_lgb_train.return_value = mock_model

    trainer = TemperatureModel("fake.csv")
    trainer.df = training_data

    with (
        COMMON_PATCHES[0],
        COMMON_PATCHES[1],
        COMMON_PATCHES[2],
        COMMON_PATCHES[3],
        COMMON_PATCHES[4],
        COMMON_PATCHES[5],
        COMMON_PATCHES[6],
        COMMON_PATCHES[7],
        patch.object(TemperatureModel, "load_and_prepare", return_value=None),
    ):
        results = trainer.run_training()

    assert "pred_tmed" in results.columns
    assert "pred_tmin" in results.columns
    assert "pred_tmax" in results.columns
    assert mock_lgb_train.call_count == 3
