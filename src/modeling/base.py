"""
Base Model Class.
Provides data loading, preprocessing, model training, evaluation, and saving functionalities.
"""

from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder

from src.config.settings import FileNames, Paths
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
        Trains LightGBM and evaluates fit.
        Args:
            X_train: Training features.
            y_train: Training target.
            X_val: Validation features.
            y_val: Validation target.
            X_test_all: Test features for all rows (for final predictions).
            X_test_eval: Test features for evaluation subset.
            y_test_eval: Test target for evaluation subset.
            target_name: Name of the target variable.
            custom_params: Optional custom LightGBM parameters.
        """
        log.info(f"🔥 Training model for: {target_name}")
        feature_names = list(X_train.columns)
        log.info(f"   📋 Features: {len(feature_names)}")

        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        params = {"verbose": -1, "force_col_wise": True}

        if custom_params:
            params.update(custom_params)
        else:
            params.update({"objective": "regression", "metric": "mae"})

        is_binary = params.get("objective") == "binary" or params.get("metric") == "auc"

        lr = params.get("learning_rate", 0.05)
        rounds = 3000 if lr < 0.03 else 1500

        model = lgb.train(
            params,
            train_data,
            num_boost_round=rounds,
            valid_sets=[train_data, val_data],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
        )

        # --- DIAGNOSIS: OVERFITTING & UNDERFITTING CHECK ---
        log.info(f"   🔎 --- DIAGNOSIS: {target_name.upper()} ---")

        preds_train = model.predict(X_train)
        preds_eval = model.predict(X_test_eval)

        if is_binary:
            # --- CLASSIFICATION (AUC) ---
            try:
                auc_train = roc_auc_score(y_train, preds_train)
                auc_test = roc_auc_score(y_test_eval, preds_eval)

                log.info(f"      AUC TRAIN: {auc_train:.4f} | AUC TEST: {auc_test:.4f}")

                if auc_train - auc_test > 0.15:
                    log.warning("      ⚠️  POTENTIAL OVERFITTING.")
                elif auc_test < 0.6:
                    log.warning("      ⚠️  POTENTIAL UNDERFITTING.")
                else:
                    log.info("      ✅  Good Fit.")
            except Exception:
                log.warning("      Could not calculate AUC.")

        else:
            # --- REGRESSION (MAE & R2) ---
            mae_train = mean_absolute_error(y_train, preds_train)
            mae_test = mean_absolute_error(y_test_eval, preds_eval)
            r2_train = r2_score(y_train, preds_train)
            r2_test = r2_score(y_test_eval, preds_eval)

            log.info(f"      MAE TRAIN: {mae_train:.3f} | MAE TEST: {mae_test:.3f}")
            log.info(f"      R2  TRAIN: {r2_train:.3f} | R2  TEST: {r2_test:.3f}")

            if mae_test > mae_train * 1.4:
                log.warning("      ⚠️  POTENTIAL OVERFITTING.")
            elif r2_train < 0.35:
                log.warning("      ⚠️  POTENTIAL UNDERFITTING.")
            else:
                log.info("      ✅  Good Fit.")

        # ---------------------------------------------------

        preds_all = model.predict(X_test_all)
        log.info(f"   📊 Predictions generated: {len(preds_all)} rows")

        # Save
        self.models[target_name] = model
        self._save_to_disk(model, target_name, feature_names)

        return preds_all

    def _save_to_disk(self, model, name: str, feature_names: list[str]):
        """Save model and feature names to disk."""
        filename = f"{FileNames.MODEL_PREFIX}{name}.pkl"
        path = Paths.MODELS / filename
        path.parent.mkdir(exist_ok=True, parents=True)

        model_data = {
            "model": model,
            "feature_names": feature_names,
        }
        joblib.dump(model_data, path)
        log.info(f"   💾 Saved: {filename}")
