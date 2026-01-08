"""
Base Model Class.
"""

from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import LabelEncoder

from src.config.settings import FileNames, ModelConfig, Paths
from src.features.transformation import FeatureEngineer
from src.utils.logger import log


class BaseModel:
    """Base class for ML models. Handles data loading, preprocessing, training, and saving."""

    def __init__(self, data_path):
        self.data_path = data_path
        self.models = {}
        self.df = None

    def load_and_prepare(self):
        """Loads and preprocesses data."""
        log.info("📂 Loading base data...")
        self.df = pd.read_csv(self.data_path)
        self.df["fecha"] = pd.to_datetime(self.df["fecha"])
        self.df = self.df.sort_values(["indicativo", "fecha"])

        # Cyclic features
        self.df = FeatureEngineer.add_time_cyclicality(self.df)

        # Station encoding
        le = LabelEncoder()
        self.df["station_id"] = le.fit_transform(self.df["indicativo"])

    def train_lgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        X_test_all: pd.DataFrame,
        X_test_eval: pd.DataFrame,
        y_test_eval: pd.Series,
        target_name: str,
        custom_params: dict[str, Any] | None = None,
    ) -> np.ndarray:
        """
        Trains LightGBM and SAVES FEATURE NAMES.
        """
        log.info(f"🔥 Training model for: {target_name}")
        feature_names = list(X_train.columns)
        log.info(f"   📋 Features: {len(feature_names)}")

        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        params = ModelConfig.LGBM_REGRESSION.copy()
        if custom_params:
            params.update(custom_params)

        rounds = 2000 if params.get("learning_rate", 0.05) < 0.05 else 1000

        model = lgb.train(
            params,
            train_data,
            num_boost_round=rounds,
            valid_sets=[train_data, val_data],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
        )

        # Evaluation
        preds_eval = model.predict(X_test_eval)
        mae = mean_absolute_error(y_test_eval, preds_eval)
        log.info(f"   🏆 TEST SET MAE {target_name}: {mae:.4f}")

        # All predictions
        preds_all = model.predict(X_test_all)
        log.info(f"   📊 Predictions generated: {len(preds_all)} rows")

        # Save
        self.models[target_name] = model
        self._save_to_disk(model, target_name, feature_names)

        return preds_all

    def _save_to_disk(self, model, name: str, feature_names: list[str]):
        """Guarda modelo Y nombres de features usando convención de nombres."""
        filename = f"{FileNames.MODEL_PREFIX}{name}.pkl"
        path = Paths.MODELS / filename
        path.parent.mkdir(exist_ok=True, parents=True)

        model_data = {
            "model": model,
            "feature_names": feature_names,
        }
        joblib.dump(model_data, path)
        log.info(f"   💾 Saved: {filename}")
