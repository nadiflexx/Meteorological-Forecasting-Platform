"""
PIPELINE 05: Recursive Multi-Step Forecasting
-----------------------------------------------
"""

from datetime import timedelta

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from tqdm import tqdm

from src.config.settings import ExperimentConfig, FeatureConfig, FileNames, Paths
from src.features.transformation import FeatureEngineer
from src.utils.logger import log


class RecursiveSimulator:
    """Simulates weather forecasts recursively for a target year using pre-trained models."""

    def __init__(self):
        self.models = {}
        self.feature_names = {}
        self._load_models()

    def _load_models(self):
        """Load pre-trained models for each target variable."""
        for t in FeatureConfig.TARGETS:
            fname = (
                FileNames.MODEL_RAIN
                if t == "rain"
                else f"{FileNames.MODEL_PREFIX}{t}.pkl"
            )
            path = Paths.MODELS / fname
            if path.exists():
                data = joblib.load(path)
                if isinstance(data, dict):
                    self.models[t] = data["model"]
                    self.feature_names[t] = data["feature_names"]

    def create_features(self, df_accumulated):
        """Create features for the accumulated dataframe up to the current simulation day."""
        cutoff_date = df_accumulated["fecha"].max() - timedelta(days=40)
        df_window = df_accumulated[df_accumulated["fecha"] >= cutoff_date].copy()

        df_window = FeatureEngineer.add_time_cyclicality(df_window)
        df_window = FeatureEngineer.add_wind_components(df_window)

        for col in FeatureConfig.LAG_COLS:
            if col in df_window.columns:
                for lag in FeatureConfig.LAGS:
                    df_window[f"{col}_lag_{lag}"] = df_window.groupby("indicativo")[
                        col
                    ].shift(lag)

        for col in ["tmed", "tmin", "tmax"]:
            if f"{col}_lag_1" in df_window.columns:
                df_window[f"{col}_trend"] = (
                    df_window[f"{col}_lag_1"] - df_window[f"{col}_lag_2"]
                )

        for col in FeatureConfig.ROLL_COLS:
            if col in df_window.columns:
                for w in FeatureConfig.WINDOWS:
                    df_window[f"{col}_roll_{w}"] = df_window.groupby("indicativo")[
                        col
                    ].transform(lambda x, w=w: x.rolling(w).mean())
        return df_window

    def run(self):
        """Run the recursive simulation pipeline."""
        log.info(
            f"🚀 INITIALIZING RECURSIVE SIMULATION ({ExperimentConfig.TARGET_YEAR})"
        )

        df_full = pd.read_csv(Paths.PROCESSED / FileNames.CLEAN_DATA)
        df_full["fecha"] = pd.to_datetime(df_full["fecha"])

        if "station_id" not in df_full.columns:
            le = LabelEncoder()
            df_full["station_id"] = le.fit_transform(df_full["indicativo"])

        cutoff_date = f"{ExperimentConfig.TARGET_YEAR}-01-01"
        df_sim = df_full[df_full["fecha"] < cutoff_date].copy()

        stations_meta = df_sim.drop_duplicates("indicativo")[
            ["indicativo", "nombre", "provincia", "altitud", "station_id"]
        ]

        start_date = pd.to_datetime(cutoff_date)
        days_to_predict = 365
        log.info(
            f"📅 Simulating from {start_date.date()} during {days_to_predict} days..."
        )

        predictions_log = []

        for i in tqdm(range(days_to_predict)):
            target_date = start_date + timedelta(days=i)

            df_feats = self.create_features(df_sim)

            # We need only the last available day per station to predict the next day
            last_day_feats = df_feats.groupby("indicativo").tail(1).copy()

            new_rows = []

            # B. Predict next day for each station
            for _, row in last_day_feats.iterrows():
                st_code = row["indicativo"]

                # Dictionary to hold the new row for the next day
                new_row = {"fecha": target_date, "indicativo": st_code}

                # Copy station metadata
                meta = stations_meta[stations_meta["indicativo"] == st_code].iloc[0]
                new_row.update(meta.to_dict())

                # Predict each target variable
                for target, model in self.models.items():
                    req_feats = self.feature_names.get(target)
                    if not req_feats:
                        continue

                    X = pd.DataFrame([row])
                    for f in req_feats:
                        if f not in X.columns:
                            X[f] = 0

                    val = model.predict(X[req_feats])[0]

                    if target == "rain":
                        new_row["prec"] = 10.0 if val > 0.5 else 0.0
                        new_row["prob_rain"] = val
                    else:
                        if target == "hrMedia":
                            val = np.clip(val, 0, 100)
                        if target == "sol":
                            val = np.clip(val, 0, 16)
                        new_row[target] = val
                        new_row[f"pred_{target}"] = val

                for col in ["presion", "nubes", "presMin", "dir", "racha"]:
                    if col not in new_row:
                        new_row[col] = row.get(col, 0)

                new_rows.append(new_row)
                predictions_log.append(new_row)

            # C. Add new day predictions to simulation dataframe
            df_next_day = pd.DataFrame(new_rows)
            df_sim = pd.concat([df_sim, df_next_day], ignore_index=True)

        # 3. Save Results
        df_res = pd.DataFrame(predictions_log)

        # Paste real values for 2025 for comparison
        df_real_2025 = df_full[df_full["fecha"].dt.year == 2025][
            ["fecha", "indicativo", "tmed", "tmin", "tmax"]
        ]
        df_res = pd.merge(
            df_res,
            df_real_2025,
            on=["fecha", "indicativo"],
            suffixes=("", "_real"),
            how="left",
        )

        output = Paths.PREDICTIONS / FileNames.FORECAST_RECURSIVE
        df_res.to_csv(output, index=False)
        log.info(f"💾 Simulation saved in: {output}")

        # 4. Analyze Degradation
        self.analyze_degradation(df_res)

    def analyze_degradation(self, df):
        """Shows how the error grows month by month."""
        log.info("\n📊 ANALYSIS OF THE DEGRADATION (Reality vs Fiction)")
        df["error_tmed"] = (df["tmed"] - df["tmed_real"]).abs()
        df["month"] = df["fecha"].dt.month

        monthly_mae = df.groupby("month")["error_tmed"].mean()
        log.info("\n📅 Monthly Mean Absolute Error (MAE):")
        log.info(monthly_mae)

        log.info(
            "\n💡 Note: Observe how the error grows. In January it will be low, in May it will be high."
        )


if __name__ == "__main__":
    RecursiveSimulator().run()
