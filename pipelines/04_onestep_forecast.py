"""
PIPELINE 04: GENERATE ONE-STEP FORECAST
This script generates one-step ahead forecasts for a specified target year using pre-trained models.
It processes the data to create necessary features and applies the models to produce predictions for various weather variables.
----------------------------------------
"""

import joblib
import numpy as np
import pandas as pd

from src.config.settings import (
    ExperimentConfig,
    FeatureConfig,
    FileNames,
    ModelConfig,
    Paths,
)
from src.features.transformation import FeatureEngineer
from src.utils.logger import log


def predict_simulation():
    """Generate one-step ahead forecasts for the target year using pre-trained models."""
    log.info(f"🚀 INITIALIZING ONE-STEP SIMULATION ({ExperimentConfig.TARGET_YEAR})")

    data_path = Paths.PROCESSED / FileNames.CLEAN_DATA
    df = pd.read_csv(data_path)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values(["indicativo", "fecha"])

    log.info("⚙️ Generating features...")
    df_eng = df.copy()
    df_eng = FeatureEngineer.add_time_cyclicality(df_eng)
    df_eng = FeatureEngineer.add_wind_components(df_eng)

    for col in FeatureConfig.LAG_COLS:
        if col in df_eng.columns:
            for lag in FeatureConfig.LAGS:
                df_eng[f"{col}_lag_{lag}"] = df_eng.groupby("indicativo")[col].shift(
                    lag
                )

    for col in ["tmed", "tmin", "tmax"]:
        if f"{col}_lag_1" in df_eng.columns:
            df_eng[f"{col}_trend"] = df_eng[f"{col}_lag_1"] - df_eng[f"{col}_lag_2"]

    for col in FeatureConfig.ROLL_COLS:
        if col in df_eng.columns:
            for w in FeatureConfig.WINDOWS:
                df_eng[f"{col}_roll_{w}"] = df_eng.groupby("indicativo")[col].transform(
                    lambda x, w=w: x.rolling(w).mean()
                )

    target_year = ExperimentConfig.TARGET_YEAR
    df_target = df_eng[df_eng["fecha"].dt.year == target_year].copy()

    if df_target.empty:
        log.error(f"❌ There is no data for the target year {target_year}.")
        return

    # Predict
    results = df_target[["fecha", "indicativo"]].copy()

    cols_reales = ["tmed", "tmin", "tmax", "prec", "sol", "hrMedia", "velmedia"]
    for col in cols_reales:
        if col in df_target.columns:
            results[f"real_{col}"] = df_target[col]

    for target in FeatureConfig.TARGETS:
        fname = (
            FileNames.MODEL_RAIN
            if target == "rain"
            else f"{FileNames.MODEL_PREFIX}{target}.pkl"
        )
        path = Paths.MODELS / fname

        if not path.exists():
            continue

        data = joblib.load(path)
        if isinstance(data, dict):
            model = data["model"]
            feat_names = data["feature_names"]
        else:
            continue

        X = df_target.copy()
        for f in feat_names:
            if f not in X.columns:
                X[f] = 0
        X = X[feat_names]

        try:
            raw_preds = model.predict(X)

            temp_series = pd.Series(raw_preds, index=results.index)
            shifted_preds = temp_series.groupby(results["indicativo"]).shift(1)

            if target == "rain":
                results["pred_prob_rain"] = shifted_preds
                results["pred_is_raining"] = (
                    shifted_preds > ModelConfig.RAIN_THRESHOLD
                ).astype(float)
            else:
                if target == "sol":
                    shifted_preds = np.clip(shifted_preds, 0, 16)
                if target == "hrMedia":
                    shifted_preds = np.clip(shifted_preds, 0, 100)

                results[f"pred_{target}"] = shifted_preds

        except Exception as e:
            log.error(f"Error predicting {target}: {e}")

    results = results.dropna(subset=["pred_tmed"])

    output_path = Paths.PREDICTIONS_COMPARATION / FileNames.FORECAST_ONESTEP
    results.to_csv(output_path, index=False)
    log.info(f"✅ Generated predictions in: {output_path}")


if __name__ == "__main__":
    predict_simulation()
