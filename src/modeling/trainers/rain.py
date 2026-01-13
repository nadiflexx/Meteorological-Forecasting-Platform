"""
Rain Classification Model.
"""

from sklearn.metrics import roc_auc_score

from src.config.settings import (
    ExperimentConfig,
    FeatureConfig,
    ModelConfig,
)
from src.features.transformation import FeatureEngineer
from src.modeling.base import BaseModel
from src.utils.logger import log


class RainClassifier(BaseModel):
    """Binary Classifier for Precipitation."""

    def run_training(self):
        self.load_and_prepare()
        df_eng = self.df.copy()

        # Feature Engineering (Lags Standard + Specifics)
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

        # Target (Binary)
        df_eng["target_rain"] = (
            df_eng.groupby("indicativo")["prec"].shift(-1) > 0.1
        ).astype(float)

        # Split
        VAL_START = ExperimentConfig.VAL_START_DATE
        TEST_START = ExperimentConfig.TEST_START_DATE

        train = df_eng[df_eng["fecha"] < VAL_START]
        val = df_eng[(df_eng["fecha"] >= VAL_START) & (df_eng["fecha"] < TEST_START)]
        test = df_eng[df_eng["fecha"] >= TEST_START]

        drop_cols = ["fecha", "indicativo", "nombre", "provincia", "target_rain"]

        # Indices with target available
        train_idx = train[train["target_rain"].notna()].index
        val_idx = val[val["target_rain"].notna()].index
        test_eval_idx = test[test["target_rain"].notna()].index

        # Datasets
        X_train = train.loc[train_idx].drop(columns=drop_cols, errors="ignore")
        y_train = train.loc[train_idx, "target_rain"].astype(int)

        X_val = val.loc[val_idx].drop(columns=drop_cols, errors="ignore")
        y_val = val.loc[val_idx, "target_rain"].astype(int)

        X_test_eval = test.loc[test_eval_idx].drop(columns=drop_cols, errors="ignore")
        y_test_eval = test.loc[test_eval_idx, "target_rain"].astype(int)

        X_test_all = test.drop(columns=drop_cols, errors="ignore")

        # Params for Classifier
        params = ModelConfig.LGBM_CLASSIFIER.copy()

        preds_all = self.train_lgbm(
            X_train,
            y_train,
            X_val,
            y_val,
            X_test_all,
            X_test_eval,
            y_test_eval,
            target_name="rain_classifier",
            custom_params=params,
        )

        model = self.models["rain_classifier"]
        probs_eval = model.predict(X_test_eval)
        auc = roc_auc_score(y_test_eval, probs_eval)
        log.info(f"   🏆 TEST SET ROC-AUC: {auc:.4f}")

        # Results
        results = test[["fecha", "indicativo", "station_id"]].copy()
        results["prob_rain"] = preds_all
        results["is_raining"] = (preds_all > ModelConfig.RAIN_THRESHOLD).astype(int)

        return results
