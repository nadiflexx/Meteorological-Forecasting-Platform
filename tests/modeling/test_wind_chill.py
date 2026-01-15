import numpy as np
import pandas as pd
from pandas.testing import assert_series_equal
import pytest

from src.modeling.wind_chill import WindChillCalculator


def vapor_pressure_tetens(t_c: pd.Series, rh: pd.Series) -> pd.Series:
    """Tetens saturation vapor pressure (hPa) and actual vapor pressure."""
    e_sat = 6.112 * np.exp((17.67 * t_c) / (t_c + 243.5))
    return (rh / 100.0) * e_sat


def expected_cold(t, v_kmh):
    """Wind Chill Index calculation for cold conditions."""
    return 13.12 + 0.6215 * t - 11.37 * (v_kmh**0.16) + 0.3965 * t * (v_kmh**0.16)


def expected_hot(t, rh):
    """Heat Index calculation for hot conditions."""
    return -8.784 + 1.611 * t + 2.338 * rh - 0.146 * (t * rh)


def expected_mid(t, rh, v_ms):
    """Steadman Apparent Temperature calculation for mild conditions."""
    e = vapor_pressure_tetens(pd.Series([t]), pd.Series([rh])).iloc[0]
    return t + (0.33 * e) - (0.70 * v_ms) - 4.00


@pytest.fixture()
def calc():
    return WindChillCalculator()


def test_returns_series_and_rounding(calc):
    df = pd.DataFrame(
        {
            "pred_tmed": [26.0],
            "pred_hrMedia": [50.0],
            "pred_velmedia": [10.0],
        }
    )
    out = calc.calculate_apparent_temp(df)

    assert isinstance(out, pd.Series)
    assert out.iloc[0] == pytest.approx(round(expected_hot(26.0, 50.0), 1))


def test_cold_case_applied_when_t_le_10_and_wind_gt_4_8_kmh(calc):
    v_input_ms = 4.9
    df = pd.DataFrame(
        {
            "pred_tmed": [10.0],
            "pred_hrMedia": [40.0],
            "pred_velmedia": [v_input_ms],
        }
    )
    out = calc.calculate_apparent_temp(df)

    v_kmh = v_input_ms * 3.6
    exp = round(expected_cold(10.0, v_kmh), 1)

    assert out.iloc[0] == pytest.approx(exp)


def test_cold_boundary_wind_low_not_applied(calc):
    v_input_ms = 1.0

    df = pd.DataFrame(
        {
            "pred_tmed": [10.0],
            "pred_hrMedia": [40.0],
            "pred_velmedia": [v_input_ms],
        }
    )
    out = calc.calculate_apparent_temp(df)

    assert out.iloc[0] == pytest.approx(10.0)


def test_hot_case_applied_when_t_ge_26(calc):
    df = pd.DataFrame(
        {
            "pred_tmed": [30.0],
            "pred_hrMedia": [70.0],
            "pred_velmedia": [1.0],
        }
    )
    out = calc.calculate_apparent_temp(df)

    exp = round(expected_hot(30.0, 70.0), 1)
    assert out.iloc[0] == pytest.approx(exp)


def test_mid_case_applied_when_10_lt_t_lt_26(calc):
    v_input_ms = 5.0
    df = pd.DataFrame(
        {
            "pred_tmed": [20.0],
            "pred_hrMedia": [60.0],
            "pred_velmedia": [v_input_ms],
        }
    )
    out = calc.calculate_apparent_temp(df)

    exp = round(expected_mid(20.0, 60.0, v_input_ms), 1)
    assert out.iloc[0] == pytest.approx(exp)


def test_mid_boundaries_not_inclusive(calc):
    # t == 10 => Cold logic check
    df1 = pd.DataFrame(
        {"pred_tmed": [10.0], "pred_hrMedia": [60.0], "pred_velmedia": [0.0]}
    )
    out1 = calc.calculate_apparent_temp(df1)
    assert out1.iloc[0] == pytest.approx(10.0)

    # t == 26 => hot (Yes)
    df2 = pd.DataFrame(
        {"pred_tmed": [26.0], "pred_hrMedia": [60.0], "pred_velmedia": [0.0]}
    )
    out2 = calc.calculate_apparent_temp(df2)
    exp2 = round(expected_hot(26.0, 60.0), 1)
    assert out2.iloc[0] == pytest.approx(exp2)


def test_multiple_rows_mixed_regimes(calc):
    df = pd.DataFrame(
        {
            "pred_tmed": [5.0, 20.0, 30.0, 10.0],
            "pred_hrMedia": [50.0, 60.0, 70.0, 40.0],
            "pred_velmedia": [
                10.0,  # Row 0: 36 km/h -> Cold Case
                5.0,  # Row 1: Mild Case (uses m/s)
                1.0,  # Row 2: Hot Case
                1.0,  # Row 3: 3.6 km/h -> < 4.8 km/h -> No Cold Form applied
            ],
        }
    )

    out = calc.calculate_apparent_temp(df)

    # Row 0: Cold. Convert 10 m/s to 36 km/h for expectation
    exp0 = round(expected_cold(5.0, 36.0), 1)

    # Row 1: Mid. Use 5.0 m/s directly
    exp1 = round(expected_mid(20.0, 60.0, 5.0), 1)

    # Row 2: Hot.
    exp2 = round(expected_hot(30.0, 70.0), 1)

    # Row 3: Boundary. 1.0 m/s = 3.6 km/h (< 4.8). Return Temp.
    exp3 = 10.0

    expected = pd.Series([exp0, exp1, exp2, exp3], name="pred_windchill")

    assert_series_equal(out.reset_index(drop=True), expected)
