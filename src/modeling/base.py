"""
Base Model Class.
Provides shared functionality for data loading and LightGBM training.
"""

from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import LabelEncoder

from src.config.settings import Paths
from src.features.transformation import FeatureEngineer
from src.utils.logger import log


class BaseModel:
    def __init__(self, data_path):
        self.data_path = data_path
        self.models = {}
        self.df = None

    def load_and_prepare(self):
        """Loads data and applies basic preprocessing common to all models."""
        log.info("📂 Loading base data...")
        self.df = pd.read_csv(self.data_path)
        self.df["fecha"] = pd.to_datetime(self.df["fecha"])
        self.df = self.df.sort_values(["indicativo", "fecha"])

        # 1. Cyclic Date Features
        self.df = FeatureEngineer.add_time_cyclicality(self.df)

        # 2. Station ID Encoding
        le = LabelEncoder()
        self.df["station_id"] = le.fit_transform(self.df["indicativo"])

    def train_lgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        target_name: str,
        custom_params: dict[str, Any] | None = None,
    ) -> np.ndarray:
        """
        Generic LightGBM Regressor Trainer.
        """
        log.info(f"🔥 Training model for: {target_name}")

        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

        # Default Parameters
        params = {
            "objective": "regression",
            "metric": "mae",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.9,
            "verbose": -1,
            "force_col_wise": True,
        }

        # Override defaults
        if custom_params:
            params.update(custom_params)

        # Increase rounds if learning rate is low
        rounds = 2000 if params.get("learning_rate", 0.05) < 0.05 else 1000

        model = lgb.train(
            params,
            train_data,
            num_boost_round=rounds,
            valid_sets=[train_data, test_data],
            callbacks=[
                lgb.early_stopping(50),
                lgb.log_evaluation(0),  # Silent
            ],
        )

        # Evaluate
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        log.info(f"   🏆 MAE {target_name}: {mae:.4f}")

        # Save
        self.models[target_name] = model
        self._save_to_disk(model, target_name)

        return preds

    def _save_to_disk(self, model, name):
        path = Paths.MODELS / f"lgbm_{name}.pkl"
        path.parent.mkdir(exist_ok=True, parents=True)
        joblib.dump(model, path)
