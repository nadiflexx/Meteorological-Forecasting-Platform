"""
Atmosphere Model Trainer.
"""

import numpy as np

from src.config.settings import ExperimentConfig, FeatureConfig
from src.features.transformation import FeatureEngineer
from src.modeling.base import BaseModel
from src.utils.logger import log


class AtmosphereModel(BaseModel):
    """Specialized trainer for volatile atmospheric variables. Handles feature engineering,
    model training, validation, and testing for solar radiation, humidity, and wind speed."""

    def run_training(self):
        self.load_and_prepare()
        targets = ["sol", "hrMedia", "velmedia"]
        df_eng = self.df.copy()

        df_eng = FeatureEngineer.add_wind_components(df_eng)

        df_eng = FeatureEngineer.create_rolling_stats(
            df_eng, FeatureConfig.ROLL_COLS, FeatureConfig.WINDOWS
        )

        cols_atmos = list(set(FeatureConfig.LAG_COLS + ["wind_sin", "wind_cos"]))
        df_eng = FeatureEngineer.create_lags(df_eng, cols_atmos, FeatureConfig.LAGS)

        df_eng = df_eng.dropna()

        VAL_START = ExperimentConfig.VAL_START_DATE
        TEST_START = ExperimentConfig.TEST_START_DATE

        train = df_eng[df_eng["fecha"] < VAL_START]
        val = df_eng[(df_eng["fecha"] >= VAL_START) & (df_eng["fecha"] < TEST_START)]
        test = df_eng[df_eng["fecha"] >= TEST_START]

        results = test[["fecha", "indicativo", "station_id"]].copy()
        cols_drop = ["fecha", "indicativo", "nombre", "provincia"]

        for target in targets:
            y_train_full = train.groupby("indicativo")[target].shift(-1)
            y_val_full = val.groupby("indicativo")[target].shift(-1)
            y_test_full = test.groupby("indicativo")[target].shift(-1)

            train_idx = y_train_full.dropna().index
            val_idx = y_val_full.dropna().index
            test_eval_idx = y_test_full.dropna().index
            test_all_idx = test.index

            X_train = train.loc[train_idx].drop(columns=cols_drop, errors="ignore")
            y_train = y_train_full.loc[train_idx]

            X_val = val.loc[val_idx].drop(columns=cols_drop, errors="ignore")
            y_val = y_val_full.loc[val_idx]

            X_test_all = test.drop(columns=cols_drop, errors="ignore")
            X_test_eval = test.loc[test_eval_idx].drop(
                columns=cols_drop, errors="ignore"
            )
            y_test_eval = y_test_full.loc[test_eval_idx]

            preds_all = self.train_lgbm(
                X_train,
                y_train,
                X_val,
                y_val,
                X_test_all,
                X_test_eval,
                y_test_eval,
                target,
            )

            preds_all = np.maximum(preds_all, 0)
            if target == "hrMedia":
                preds_all = np.minimum(preds_all, 100)
            if target == "sol":
                preds_all = np.minimum(preds_all, 16)

            results.loc[test_all_idx, f"pred_{target}"] = preds_all

        log.info(f"   📊 Atmosphere results: {len(results)} rows")
        return results
