"""
Base Model Class.

Provides shared functionality for data loading, preprocessing,
and a standardized interface for LightGBM training.
This acts as a parent class to ensure consistency across all specific trainers.
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
    """
    Abstract base class for Machine Learning tasks.

    Responsibilities:
    1.  **Data Loading**: Reads the processed CSV and ensures correct types.
    2.  **Feature Engineering**: Applies global transformations (e.g., Cyclical Time).
    3.  **Training Abstraction**: Wraps the LightGBM boilerplate code (Dataset creation,
        hyperparameters, early stopping, and saving) into a reusable method.
    """

    def __init__(self, data_path):
        self.data_path = data_path
        self.models = {}  # Dictionary to store trained model objects
        self.df = None  # Will hold the loaded DataFrame

    def load_and_prepare(self):
        """
        Loads data from disk and applies common preprocessing steps.

        Operations:
        - Parses dates.
        - Sorts by Station and Date (critical for time-series).
        - Generates Cyclical Features (Sine/Cosine for months).
        - Encodes categorical Station IDs into integers.
        """
        log.info("📂 Loading base data...")
        self.df = pd.read_csv(self.data_path)
        self.df["fecha"] = pd.to_datetime(self.df["fecha"])
        self.df = self.df.sort_values(["indicativo", "fecha"])

        # 1. Cyclic Date Features (Month_sin, Month_cos, etc.)
        self.df = FeatureEngineer.add_time_cyclicality(self.df)

        # 2. Station ID Encoding
        le = LabelEncoder()
        self.df["station_id"] = le.fit_transform(self.df["indicativo"])

    def train_lgbm(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        target_name: str,
        custom_params: dict[str, Any] | None = None,
    ) -> np.ndarray:
        """
        Generic trainer for LightGBM Regressors using 3-Way Split (Train/Val/Test).

        Encapsulates the training lifecycle:
        1. Creates lgb.Dataset objects for Train and Validation.
        2. Configures hyperparameters (with optional overrides).
        3. Runs training with Early Stopping monitoring the Validation set.
        4. Logs performance metrics (MAE) on the completely unseen Test set.
        5. Persists the trained model to disk (.pkl).

        Args:
            X_train, y_train: Training data (Model learns from this).
            X_val, y_val: Validation data (Used for Early Stopping).
            X_test, y_test: Test data (Used ONLY for final evaluation).
            target_name (str): Name of the variable (used for logging and filenames).
            custom_params (dict, optional): LightGBM hyperparameter overrides.

        Returns:
            np.ndarray: Predictions for the test set.
        """
        log.info(f"🔥 Training model for: {target_name}")

        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

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

        # Run Training
        model = lgb.train(
            params,
            train_data,
            num_boost_round=rounds,
            valid_sets=[train_data, val_data],
            callbacks=[
                lgb.early_stopping(50),  # Stop if no improvement in 50 rounds
                lgb.log_evaluation(0),
            ],
        )

        # Evaluate Performance (On the unseen Test Set)
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        log.info(f"   🏆 TEST SET MAE {target_name}: {mae:.4f}")

        # Save
        self.models[target_name] = model
        self._save_to_disk(model, target_name)

        return preds

    def _save_to_disk(self, model, name):
        """Helper to serialize model objects to the 'models/' directory."""

        path = Paths.MODELS / f"lgbm_{name}.pkl"
        path.parent.mkdir(exist_ok=True, parents=True)
        joblib.dump(model, path)
