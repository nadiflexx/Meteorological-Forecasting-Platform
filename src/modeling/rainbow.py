"""
Rainbow Heuristic Engine.

This module contains the logic to derive a 'Rainbow Probability' score
by combining the outputs of the distinct Machine Learning models
(Rain Classifier + Solar Regressor + Humidity Regressor).
"""

import numpy as np
import pandas as pd


class RainbowCalculator:
    """
    Implements the physics-based heuristic rules to estimate rainbow occurrence.
    """

    def calculate_probability(self, df_preds: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the final probability score (0-100%).

        Args:
            df_preds (pd.DataFrame): DataFrame containing ML predictions.

        Returns:
            pd.DataFrame: The input DataFrame with a new 'rainbow_prob' column.
        """
        df = df_preds.copy()

        # ---------------------------------------------------------
        # 1. RAIN FACTOR (Precipitation Probability)
        # ---------------------------------------------------------
        conditions_rain = [
            (df["prob_rain"] < 0.25),
            (df["prob_rain"] >= 0.25) & (df["prob_rain"] <= 0.85),
            (df["prob_rain"] > 0.85),
        ]
        values_rain = [0.0, 1.0, 0.7]

        df["score_rain"] = np.select(conditions_rain, values_rain)
        df["score_rain"] = df["score_rain"] * df["prob_rain"]

        # ---------------------------------------------------------
        # 2. SUN FACTOR (Insolation Hours)
        # ---------------------------------------------------------
        conditions_sol = [
            (df["pred_sol"] < 1.0),
            (df["pred_sol"] >= 1.0) & (df["pred_sol"] < 4.0),
            (df["pred_sol"] >= 4.0) & (df["pred_sol"] < 10.0),
            (df["pred_sol"] >= 10.0),
        ]
        values_sol = [0.0, 0.6, 1.0, 0.8]

        df["score_sol"] = np.select(conditions_sol, values_sol)

        # ---------------------------------------------------------
        # 3. HUMIDITY FACTOR (Mean Relative Humidity)
        # ---------------------------------------------------------
        df["factor_humedad"] = df["pred_hrMedia"] / 100.0
        df.loc[df["pred_hrMedia"] < 40, "factor_humedad"] *= 0.5

        # ---------------------------------------------------------
        # FINAL FORMULA
        # ---------------------------------------------------------
        raw_prob = (df["score_rain"] * df["score_sol"] * df["factor_humedad"]) * 120
        df["rainbow_prob"] = raw_prob.clip(0, 95).round(1)

        # ---------------------------------------------------------
        # CLEANUP: Remove intermediate calculation columns
        # ---------------------------------------------------------
        df = df.drop(
            columns=["score_rain", "score_sol", "factor_humedad"], errors="ignore"
        )

        return df
