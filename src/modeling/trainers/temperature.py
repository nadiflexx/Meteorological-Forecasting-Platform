"""
Temperature Model Trainer.
"""

from src.config.settings import ExperimentConfig, FeatureConfig, ModelConfig
from src.modeling.base import BaseModel
from src.utils.logger import log


class TemperatureModel(BaseModel):
    """Specialized trainer for Temperature forecasting. Implements
    feature engineering, data splitting, and model training specific to temperature prediction."""

    def run_training(self):
        self.load_and_prepare()
        targets = ["tmed", "tmin", "tmax"]

        df_eng = self.df.copy()

        # A. LAGS
        for col in FeatureConfig.LAG_COLS:
            if col in df_eng.columns:
                for lag in FeatureConfig.LAGS:
                    df_eng[f"{col}_lag_{lag}"] = df_eng.groupby("indicativo")[
                        col
                    ].shift(lag)

        # B. DELTAS / TRENDS
        for col in ["tmed", "tmin", "tmax"]:
            if f"{col}_lag_1" in df_eng.columns:
                df_eng[f"{col}_trend"] = df_eng[f"{col}_lag_1"] - df_eng[f"{col}_lag_2"]

        # C. ROLLING
        for w in FeatureConfig.WINDOWS:
            if "tmed" in df_eng.columns:
                df_eng[f"tmed_roll_{w}"] = df_eng.groupby("indicativo")[
                    "tmed"
                ].transform(lambda x, w=w: x.rolling(w).mean())

        df_eng = df_eng.dropna()

        # --- Train/Validation/Test Split---
        VAL_START = ExperimentConfig.VAL_START_DATE
        TEST_START = ExperimentConfig.TEST_START_DATE

        train = df_eng[df_eng["fecha"] < VAL_START]
        val = df_eng[(df_eng["fecha"] >= VAL_START) & (df_eng["fecha"] < TEST_START)]
        test = df_eng[df_eng["fecha"] >= TEST_START]

        results = test[["fecha", "indicativo", "station_id"]].copy()
        cols_drop = ["fecha", "indicativo", "nombre", "provincia"]

        for target in targets:
            if target not in df_eng.columns:
                continue

            y_train_full = train.groupby("indicativo")[target].shift(-1)
            y_val_full = val.groupby("indicativo")[target].shift(-1)
            y_test_full = test.groupby("indicativo")[target].shift(-1)

            train_valid_idx = y_train_full.dropna().index
            val_valid_idx = y_val_full.dropna().index
            test_eval_idx = y_test_full.dropna().index
            test_all_idx = test.index

            X_train = train.loc[train_valid_idx].drop(
                columns=cols_drop, errors="ignore"
            )
            y_train = y_train_full.loc[train_valid_idx]

            X_val = val.loc[val_valid_idx].drop(columns=cols_drop, errors="ignore")
            y_val = y_val_full.loc[val_valid_idx]

            X_test_all = test.drop(columns=cols_drop, errors="ignore")
            X_test_eval = test.loc[test_eval_idx].drop(
                columns=cols_drop, errors="ignore"
            )
            y_test_eval = y_test_full.loc[test_eval_idx]

            custom_params = {}
            if target == "tmed":
                custom_params = ModelConfig.LGBM_TMED
            elif target == "tmin":
                custom_params = ModelConfig.LGBM_TMIN
            elif target == "tmax":
                custom_params = ModelConfig.LGBM_TMAX

            preds_all = self.train_lgbm(
                X_train,
                y_train,
                X_val,
                y_val,
                X_test_all,
                X_test_eval,
                y_test_eval,
                target,
                custom_params=custom_params,
            )
            results.loc[test_all_idx, f"pred_{target}"] = preds_all

        log.info(f"   📊 Temperature results: {len(results)} rows")
        return results
