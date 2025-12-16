"""
Atmosphere Model Trainer.
Predicts: Solar Radiation, Humidity (Direct), and Wind Speed.
Strategy: Direct regression using Pressue/Cloud context (No Physics Engine).
"""

import numpy as np

from src.features.transformation import FeatureEngineer
from src.modeling.base import BaseModel


class AtmosphereModel(BaseModel):
    def run_training(self):
        self.load_and_prepare()

        # Volvemos a predecir hrMedia directamente
        targets = ["sol", "hrMedia", "velmedia"]
        df_eng = self.df.copy()

        # ---------------------------------------------------------
        # 1. FEATURES
        # ---------------------------------------------------------
        # Viento Vectorial
        df_eng = FeatureEngineer.add_wind_components(df_eng)

        # ---------------------------------------------------------
        # 2. TEMPORAL FEATURES (Contexto Histórico)
        # ---------------------------------------------------------
        # Rolling sobre variables clave para captar tendencias
        roll_cols = ["hrMedia", "presion", "nubes"]
        df_eng = FeatureEngineer.create_rolling_stats(df_eng, roll_cols, [3, 7])

        # Lags
        lag_cols = [
            "hrMedia",
            "presion",
            "nubes",
            "velmedia",
            "sol",
            "tmed",
            "wind_sin",
            "wind_cos",
            "hrMedia_roll_3",
            "presion_roll_3",
        ]
        df_eng = FeatureEngineer.create_lags(df_eng, lag_cols, [1, 2])

        # ---------------------------------------------------------
        # 3. TRAINING LOOP
        # ---------------------------------------------------------
        df_eng = df_eng.dropna()
        cutoff = "2023-01-01"
        train = df_eng[df_eng["fecha"] < cutoff]
        test = df_eng[df_eng["fecha"] >= cutoff]

        results = test[["fecha", "indicativo"]].copy()

        for target in targets:
            y_train = train.groupby("indicativo")[target].shift(-1).dropna()
            y_test = test.groupby("indicativo")[target].shift(-1).dropna()

            cols_drop = ["fecha", "indicativo", "nombre", "provincia"]
            X_train = train.loc[y_train.index].drop(columns=cols_drop, errors="ignore")
            X_test = test.loc[y_test.index].drop(columns=cols_drop, errors="ignore")

            # Hiperparámetros específicos para Humedad directa
            params = None
            if target == "hrMedia":
                params = {
                    "objective": "regression",
                    "metric": "mse",  # Penalizar errores grandes
                    "num_leaves": 50,
                    "learning_rate": 0.03,
                    "colsample_bytree": 0.8,
                    "n_estimators": 2000,
                }

            preds = self.train_lgbm(X_train, y_train, X_test, y_test, target, params)

            # Clips físicos
            preds = np.maximum(preds, 0)
            if target == "hrMedia":
                preds = np.minimum(preds, 100)
            if target == "sol":
                preds = np.minimum(preds, 16)

            results.loc[y_test.index, f"pred_{target}"] = preds

        return results.dropna()
