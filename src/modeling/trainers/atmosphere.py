"""
Atmosphere Model Trainer.

Predicts secondary meteorological variables: Solar Radiation,
Relative Humidity, and Wind Speed.
Strategy: Direct regression using Pressure/Cloud context.
"""

import numpy as np

from src.features.transformation import FeatureEngineer
from src.modeling.base import BaseModel


class AtmosphereModel(BaseModel):
    """
    Specialized trainer for volatile atmospheric variables.

    This class handles the regression for:
    1.  **Solar Radiation ('sol')**: Critical for the Rainbow heuristic.
    2.  **Relative Humidity ('hrMedia')**: Hard to predict due to high variance.
    3.  **Wind Speed ('velmedia')**: Dependent on pressure gradients.
    """

    def run_training(self):
        """
        Executes the training pipeline for atmospheric variables.

        Workflow:
        1.  **Vectorization**: Converts Wind Direction (degrees) into Sin/Cos components
            to handle the circular nature of the data (0° vs 360°).
        2.  **Trend Analysis**: Calculates Rolling Means (3-day, 7-day) for Pressure and Humidity.
        3.  **Data Splitting**: Uses Train (2009-2020), Val (2021-2022), Test (2023-2025).
        4.  **Training**: Runs LightGBM regressors with specific tuning for Humidity.
        5.  **Post-Processing**: Clips predictions to ensure physical realism.

        Returns:
            pd.DataFrame: DataFrame containing predictions for the Test set.
        """
        self.load_and_prepare()

        # Targets to predict directly
        targets = ["sol", "hrMedia", "velmedia"]
        df_eng = self.df.copy()

        # ---------------------------------------------------------
        # 1. FEATURE ENGINEERING: PHYSICS
        # ---------------------------------------------------------
        # Wind Vectorization:
        # We transform 'direction' (0-360) into u,v components to avoid
        # numerical discontinuity between 359° and 1°.
        df_eng = FeatureEngineer.add_wind_components(df_eng)

        # ---------------------------------------------------------
        # 2. FEATURE ENGINEERING: TEMPORAL CONTEXT
        # ---------------------------------------------------------
        # Rolling statistics to capture short-term trends (e.g., increasing pressure)
        roll_cols = ["hrMedia", "presion", "nubes"]
        df_eng = FeatureEngineer.create_rolling_stats(df_eng, roll_cols, [3, 7])

        # Lagged features (Yesterday's values)
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

        # --- 3-WAY SPLIT LOGIC ---
        VAL_START = "2021-01-01"
        TEST_START = "2023-01-01"

        train = df_eng[df_eng["fecha"] < VAL_START]
        val = df_eng[(df_eng["fecha"] >= VAL_START) & (df_eng["fecha"] < TEST_START)]
        test = df_eng[df_eng["fecha"] >= TEST_START]

        results = test[["fecha", "indicativo"]].copy()

        for target in targets:
            # Shift target by -1 to predict "Tomorrow"
            y_train = train.groupby("indicativo")[target].shift(-1).dropna()
            y_val = val.groupby("indicativo")[target].shift(-1).dropna()
            y_test = test.groupby("indicativo")[target].shift(-1).dropna()

            cols_drop = ["fecha", "indicativo", "nombre", "provincia"]

            # Prepare feature matrices
            X_train = train.loc[y_train.index].drop(columns=cols_drop, errors="ignore")
            X_val = val.loc[y_val.index].drop(columns=cols_drop, errors="ignore")
            X_test = test.loc[y_test.index].drop(columns=cols_drop, errors="ignore")

            # Specific Hyperparameters for Humidity
            # Humidity is noisy; we use MSE to penalize large errors heavily
            # and lower the learning rate for stability.
            params = None
            if target == "hrMedia":
                params = {
                    "objective": "regression",
                    "metric": "mse",
                    "num_leaves": 50,
                    "learning_rate": 0.03,
                    "colsample_bytree": 0.8,
                    "n_estimators": 2000,
                }

            # Train Model (Using 3 sets)
            preds = self.train_lgbm(
                X_train, y_train, X_val, y_val, X_test, y_test, target, params
            )

            # Physical Constraints (Post-processing)
            # Clip values to stay within laws of physics
            preds = np.maximum(preds, 0)  # No negative wind or sun
            if target == "hrMedia":
                preds = np.minimum(preds, 100)  # Max 100% Humidity
            if target == "sol":
                preds = np.minimum(preds, 16)  # Max ~15h sun in summer

            results.loc[y_test.index, f"pred_{target}"] = preds

        return results.dropna()
