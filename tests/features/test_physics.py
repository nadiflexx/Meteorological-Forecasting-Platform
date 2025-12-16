import numpy as np
import pandas as pd

from src.features.physics import PhysicsEngine


def test_relative_humidity_calculation():
    # Caso: T = 20°C, Td = 20°C -> HR debe ser 100%
    temp = pd.Series([20.0])
    dew = pd.Series([20.0])

    hr = PhysicsEngine.calculate_relative_humidity(temp, dew)
    assert np.isclose(hr[0], 100.0, atol=0.1)


def test_relative_humidity_dry():
    # Caso: T = 30°C, Td = 10°C -> HR debe ser baja (~28%)
    temp = pd.Series([30.0])
    dew = pd.Series([10.0])

    hr = PhysicsEngine.calculate_relative_humidity(temp, dew)
    assert 25.0 < hr[0] < 35.0


def test_vpd_calculation():
    # VPD debe ser positivo si T > Td
    temp = pd.Series([25.0])
    dew = pd.Series([15.0])

    vpd = PhysicsEngine.calculate_vapor_pressure_deficit(temp, dew)
    assert vpd[0] > 0
