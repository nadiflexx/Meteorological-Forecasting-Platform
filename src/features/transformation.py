"""
Feature Engineering Utilities.
Common transformations for time-series forecasting.
"""

import numpy as np
import pandas as pd


class FeatureEngineer:
    @staticmethod
    def add_time_cyclicality(df: pd.DataFrame, date_col: str = "fecha") -> pd.DataFrame:
        """Adds Sine/Cosine features for Month and DayOfYear."""
        df["month_sin"] = np.sin(2 * np.pi * df[date_col].dt.month / 12)
        df["month_cos"] = np.cos(2 * np.pi * df[date_col].dt.month / 12)

        # Day of year (finer granularity)
        doy = df[date_col].dt.dayofyear
        df["day_sin"] = np.sin(2 * np.pi * doy / 365.0)
        df["day_cos"] = np.cos(2 * np.pi * doy / 365.0)
        return df

    @staticmethod
    def add_wind_components(df: pd.DataFrame, dir_col: str = "dir") -> pd.DataFrame:
        """Converts wind direction (degrees) to vector components (u, v)."""
        if dir_col in df.columns:
            # Clean invalid values (99 usually means variable/calm in METAR, mapped to 0)
            clean_dir = df[dir_col].fillna(0).replace(99, 0)
            rads = np.deg2rad(clean_dir)
            df["wind_sin"] = np.sin(rads)
            df["wind_cos"] = np.cos(rads)
        return df

    @staticmethod
    def create_lags(
        df: pd.DataFrame,
        cols: list[str],
        lags: list[int],
        group_col: str = "indicativo",
    ) -> pd.DataFrame:
        """Creates Lag features for specified columns."""
        for col in cols:
            if col in df.columns:
                for lag in lags:
                    df[f"{col}_lag_{lag}"] = df.groupby(group_col)[col].shift(lag)
        return df

    @staticmethod
    def create_rolling_stats(
        df: pd.DataFrame,
        cols: list[str],
        windows: list[int],
        group_col: str = "indicativo",
    ) -> pd.DataFrame:
        """Creates Rolling Mean features."""
        for col in cols:
            if col in df.columns:
                for w in windows:
                    df[f"{col}_roll_{w}"] = df.groupby(group_col)[col].transform(
                        lambda x: x.rolling(w).mean()
                    )
        return df
