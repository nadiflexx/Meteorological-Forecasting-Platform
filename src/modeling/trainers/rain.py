"""
Rain Classification Model.
"""

import joblib
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

from src.config.settings import (
    ExperimentConfig,
    FeatureConfig,
    FileNames,
    ModelConfig,
    Paths,
)
from src.features.transformation import FeatureEngineer
from src.modeling.base import BaseModel
from src.utils.logger import log


class RainClassifier(BaseModel):
    """Binary Classifier for Precipitation. Predicts if it will rain (>0.1mm) the next hour."""

    def run_training(self):
        self.load_and_prepare()
        df_eng = self.df.copy()

        if "presion" in df_eng.columns:
            df_eng["presion_diff"] = df_eng.groupby("indicativo")["presion"].diff()
        if "nubes" in df_eng.columns and "hrMedia" in df_eng.columns:
            df_eng["cloud_moisture"] = df_eng["nubes"] * df_eng["hrMedia"]

        rain_cols = FeatureConfig.LAG_COLS + ["presion_diff", "cloud_moisture"]
        df_eng = FeatureEngineer.create_lags(df_eng, rain_cols, FeatureConfig.LAGS)
        df_eng = FeatureEngineer.create_rolling_stats(
            df_eng, ["presion"], FeatureConfig.WINDOWS
        )

        df_eng = df_eng.dropna()

        # Target
        df_eng["target_rain"] = (
            df_eng.groupby("indicativo")["prec"].shift(-1) > 0.1
        ).astype(float)

        VAL_START = ExperimentConfig.VAL_START_DATE
        TEST_START = ExperimentConfig.TEST_START_DATE

        train = df_eng[df_eng["fecha"] < VAL_START]
        val = df_eng[(df_eng["fecha"] >= VAL_START) & (df_eng["fecha"] < TEST_START)]
        test = df_eng[df_eng["fecha"] >= TEST_START]

        drop_cols = ["fecha", "indicativo", "nombre", "provincia", "target_rain"]

        train_valid = train[train["target_rain"].notna()]
        X_train = train_valid.drop(columns=drop_cols, errors="ignore")
        y_train = train_valid["target_rain"].astype(int)

        val_valid = val[val["target_rain"].notna()]
        X_val = val_valid.drop(columns=drop_cols, errors="ignore")
        y_val = val_valid["target_rain"].astype(int)

        test_eval = test[test["target_rain"].notna()]
        X_test_eval = test_eval.drop(columns=drop_cols, errors="ignore")
        y_test_eval = test_eval["target_rain"].astype(int)

        X_test_all = test.drop(columns=drop_cols, errors="ignore")

        feature_names = list(X_train.columns)
        log.info(f"☔ Training Rain Classifier ({len(feature_names)} features)...")

        # Train
        train_ds = lgb.Dataset(X_train, label=y_train)
        val_ds = lgb.Dataset(X_val, label=y_val, reference=train_ds)

        # Params
        params = ModelConfig.LGBM_CLASSIFIER.copy()

        model = lgb.train(
            params,
            train_ds,
            num_boost_round=1500,
            valid_sets=[train_ds, val_ds],
            callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)],
        )

        # Evaluate & Predict
        probs_eval = model.predict(X_test_eval)
        auc = roc_auc_score(y_test_eval, probs_eval)
        log.info(f"   🏆 TEST SET ROC-AUC: {auc:.4f}")

        probs_all = model.predict(X_test_all)

        # Save
        path = Paths.MODELS / FileNames.MODEL_RAIN
        path.parent.mkdir(exist_ok=True)
        joblib.dump({"model": model, "feature_names": feature_names}, path)
        log.info("   💾 Saved rain classifier")

        results = test[["fecha", "indicativo", "station_id"]].copy()
        results["prob_rain"] = probs_all
        results["is_raining"] = (probs_all > ModelConfig.RAIN_THRESHOLD).astype(int)

        return results
