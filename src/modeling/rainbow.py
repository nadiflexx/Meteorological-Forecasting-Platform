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

    Since historical data for rainbows does not exist in standard meteorological
    datasets, we cannot train a direct ML model for it. Instead, we use a
    **Probabilistic Inference** approach based on atmospheric physics.

    The Logic:
    Rainbows require a specific "Goldilocks Zone":
    1.  **Water**: It must be raining (High Rain Probability).
    2.  **Light**: Direct sunlight must hit the droplets (High Insolation).
    3.  **Geometry**: The sun must be relatively low (< 42 degrees),
        though we approximate this via time-of-year and sun hours.
    """

    def calculate_probability(self, df_preds: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the final probability score (0-100%).

        Args:
            df_preds (pd.DataFrame): DataFrame containing ML predictions:
                - 'prob_rain': Probability of rain (0.0 - 1.0).
                - 'pred_sol': Predicted hours of sunshine.
                - 'pred_hrMedia': Predicted relative humidity (%).

        Returns:
            pd.DataFrame: The input DataFrame with a new 'rainbow_prob' column.
        """
        df = df_preds.copy()

        # ---------------------------------------------------------
        # 1. RAIN FACTOR (Precipitation Probability)
        # ---------------------------------------------------------
        # We need rain, but a 99% probability often implies a thick,
        # gray overcast sky (Stratocumulus), which blocks the sun.
        # We prefer "Scattered Showers" (unstable weather).
        conditions_rain = [
            (df["prob_rain"] < 0.25),  # Too dry -> 0% chance
            (df["prob_rain"] >= 0.25)
            & (df["prob_rain"] <= 0.85),  # IDEAL: Scattered/Broken showers
            (df["prob_rain"] > 0.85),  # General heavy rain (Gray sky penalty)
        ]
        values_rain = [
            0.0,
            1.0,  # Max score
            0.7,  # Penalty for potential lack of sun breaks
        ]

        df["score_rain"] = np.select(conditions_rain, values_rain)

        # Nuance: Weight by the actual probability to differentiate 30% from 80%
        df["score_rain"] = df["score_rain"] * df["prob_rain"]

        # ---------------------------------------------------------
        # 2. SUN FACTOR (Insolation Hours)
        # ---------------------------------------------------------
        # Based on daily insolation (0 to 15 hours):
        # - < 1h: Total Overcast/Dark. No light source.
        # - 1h - 4h: Mostly cloudy, but with breaks. Possible.
        # - 4h - 10h: IDEAL. "Sun & Clouds" mix. Dynamic weather.
        # - > 10h: Mostly Clear. Hard to coincide with rain, but if it happens, it's a sure hit.

        conditions_sol = [
            (df["pred_sol"] < 1.0),  # Too cloudy
            (df["pred_sol"] >= 1.0) & (df["pred_sol"] < 4.0),  # Cloudy with breaks
            (df["pred_sol"] >= 4.0) & (df["pred_sol"] < 10.0),  # IDEAL (Variable)
            (df["pred_sol"] >= 10.0),  # Very sunny
        ]
        # Scoring
        values_sol = [0.0, 0.6, 1.0, 0.8]

        df["score_sol"] = np.select(conditions_sol, values_sol)

        # ---------------------------------------------------------
        # 3. HUMIDITY FACTOR (Mean Relative Humidity)
        # ---------------------------------------------------------
        # Rainbows favor high humidity with good visibility.
        # Very low humidity (<40%) causes droplets to evaporate too fast.
        df["factor_humedad"] = df["pred_hrMedia"] / 100.0

        # Penalty for dry air
        df.loc[df["pred_hrMedia"] < 40, "factor_humedad"] *= 0.5

        # ---------------------------------------------------------
        # FINAL FORMULA
        # ---------------------------------------------------------
        # Probability = (Rain Score * Sun Score * Humidity Factor)
        # We multiply by 120 (1.2 scaling) to be slightly optimistic,
        # as exact simultaneous conditions are mathematically rare in daily averages.
        raw_prob = (df["score_rain"] * df["score_sol"] * df["factor_humedad"]) * 120

        # Clip to a realistic maximum of 95% and round
        df["rainbow_prob"] = raw_prob.clip(0, 95).round(1)

        return df[
            [
                "fecha",
                "indicativo",
                "rainbow_prob",
                "prob_rain",
                "is_raining",
                "pred_sol",
                "pred_hrMedia",  # Useful for debugging/audit
            ]
        ]
