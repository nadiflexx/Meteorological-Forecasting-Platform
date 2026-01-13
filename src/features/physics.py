"""
Physics Engine.
Thermodynamic calculations for meteorological variables.
"""

import numpy as np
import pandas as pd


class PhysicsEngine:
    """Static class for physical conversions."""

    @staticmethod
    def calculate_saturation_vapor_pressure(temp_series: pd.Series) -> pd.Series:
        """
        Magnus formula for Saturation Vapor Pressure (Es) in hPa.
        Args:
            temp_series: Temperature in Celsius.
        """
        a = 17.625
        b = 243.04
        return 6.1094 * np.exp((a * temp_series) / (b + temp_series))

    @staticmethod
    def calculate_vapor_pressure(dew_point_series: pd.Series) -> pd.Series:
        """
        Magnus formula for Actual Vapor Pressure (Ea) using Dew Point.
        """
        a = 17.625
        b = 243.04
        return 6.1094 * np.exp((a * dew_point_series) / (b + dew_point_series))

    @staticmethod
    def calculate_vapor_pressure_deficit(
        temp_series: pd.Series, dew_point_series: pd.Series
    ) -> pd.Series:
        """
        Calculates VPD (The drying power of air).
        VPD = Es - Ea
        """
        es = PhysicsEngine.calculate_saturation_vapor_pressure(temp_series)
        ea = PhysicsEngine.calculate_vapor_pressure(dew_point_series)
        return es - ea

    @staticmethod
    def calculate_relative_humidity(
        temp_series: pd.Series, dew_point_series: pd.Series
    ) -> pd.Series:
        """
        Calculates Relative Humidity (%) from Temperature and Dew Point.
        """
        es = PhysicsEngine.calculate_saturation_vapor_pressure(temp_series)
        ea = PhysicsEngine.calculate_vapor_pressure(dew_point_series)

        hr = 100 * (ea / es)
        return hr.clip(0, 100)

    @staticmethod
    def calculate_dew_point_depression(
        temp_series: pd.Series, dew_point_series: pd.Series
    ) -> pd.Series:
        """Simple difference T - Td."""
        return temp_series - dew_point_series
