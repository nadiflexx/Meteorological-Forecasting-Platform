"""
Wind Chill Engine.

This module contains the logic to derive a 'Wind Chill prediction'
by combining the outputs of the distinct Machine Learning models
(Rain Classifier +  Wind velocity Regressor + Humidity Regressor).
"""

import numpy as np
import pandas as pd


class WindChillCalculator:
    """ """

    def calculate_apparent_temp(self, df_preds: pd.DataFrame) -> pd.DataFrame:
        """
        Computes the 'pred_windchill' column.

        Args:
            df_preds (pd.DataFrame):
        - 'pred_tmed': Predicted dry temperature (°C).
        - 'pred_hrMedia': Predicted relative humidity (%).
        - 'pred_velmedia': Predicted wind speed (km/h).
        """
        df = df_preds.copy()

        def get_vapor_pressure(t, h):
            e_sat = 6.112 * np.exp((17.67 * t) / (t + 243.5))
            return (h / 100.0) * e_sat

        df["pred_windchill"] = df["pred_tmed"]

        # --- CASE 1: WIND CHILL (COLD) ---
        mask_cold = (df["pred_tmed"] <= 10) & (df["pred_velmedia"] > 4.8)
        df.loc[mask_cold, "pred_windchill"] = (
            13.12
            + 0.6215 * df["pred_tmed"]
            - 11.37 * (df["pred_velmedia"] ** 0.16)
            + 0.3965 * df["pred_tmed"] * (df["pred_velmedia"] ** 0.16)
        )

        # --- CASE 2: HEAT INDEX (Hot) ---
        mask_hot = df["pred_tmed"] >= 26
        # Rothfusz regression
        df.loc[mask_hot, "pred_windchill"] = (
            -8.784
            + 1.611 * df["pred_tmed"]
            + 2.338 * df["pred_hrMedia"]
            - 0.146 * (df["pred_tmed"] * df["pred_hrMedia"])
        )

        # --- CASE 3: STEADMAN (MILD: 10°C < T < 26°C) ---
        mask_mid = (df["pred_tmed"] > 10) & (df["pred_tmed"] < 26)

        e = get_vapor_pressure(df["pred_tmed"], df["pred_hrMedia"])

        df.loc[mask_mid, "pred_windchill"] = (
            df["pred_tmed"] + (0.33 * e) - (0.70 * df["pred_velmedia"]) - 4.00
        )

        df["pred_windchill"] = df["pred_windchill"].round(1)

        return df["pred_windchill"]
