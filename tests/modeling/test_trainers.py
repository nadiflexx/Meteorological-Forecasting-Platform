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
    return pd.DataFrame(
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


def mock_predict(X, *args, **kwargs):
    return np.array([0.5] * len(X))


@patch("src.modeling.base.lgb.train")
@patch("src.modeling.base.joblib.dump")
def test_rain_classifier_flow(mock_dump, mock_lgb_train, training_data):
    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_predict
    mock_lgb_train.return_value = mock_model

    trainer = RainClassifier("fake.csv")
    trainer.df = training_data

    with patch.object(RainClassifier, "load_and_prepare", return_value=None):
        results = trainer.run_training()

    assert mock_lgb_train.called
    assert "prob_rain" in results.columns


@patch("src.modeling.base.lgb.train")
@patch("src.modeling.base.joblib.dump")
def test_atmosphere_regressor_flow(mock_dump, mock_lgb_train, training_data):
    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_predict
    mock_lgb_train.return_value = mock_model

    trainer = AtmosphereModel("fake.csv")
    trainer.df = training_data

    with patch.object(AtmosphereModel, "load_and_prepare", return_value=None):
        results = trainer.run_training()

    assert "pred_sol" in results.columns


@patch("src.modeling.base.lgb.train")
@patch("src.modeling.base.joblib.dump")
def test_temperature_regressor_flow(mock_dump, mock_lgb_train, training_data):
    mock_model = MagicMock()
    mock_model.predict.side_effect = mock_predict
    mock_lgb_train.return_value = mock_model

    trainer = TemperatureModel("fake.csv")
    trainer.df = training_data

    with patch.object(TemperatureModel, "load_and_prepare", return_value=None):
        results = trainer.run_training()

    assert "pred_tmed" in results.columns
    assert mock_lgb_train.call_count == 3
