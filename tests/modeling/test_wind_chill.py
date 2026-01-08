import numpy as np
import pandas as pd
from pandas.testing import assert_series_equal
import pytest

from src.modeling.wind_chill import WindChillCalculator


def vapor_pressure_tetens(t_c: pd.Series, rh: pd.Series) -> pd.Series:
    """Tetens saturation vapor pressure (hPa) and actual vapor pressure."""
    e_sat = 6.112 * np.exp((17.67 * t_c) / (t_c + 243.5))
    return (rh / 100.0) * e_sat


def expected_cold(t, v):
    return 13.12 + 0.6215 * t - 11.37 * (v**0.16) + 0.3965 * t * (v**0.16)


def expected_hot(t, rh):
    return -8.784 + 1.611 * t + 2.338 * rh - 0.146 * (t * rh)


def expected_mid(t, rh, v):
    e = vapor_pressure_tetens(pd.Series([t]), pd.Series([rh])).iloc[0]
    return t + (0.33 * e) - (0.70 * v) - 4.00


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
    # Debe estar redondeado a 1 decimal
    assert out.iloc[0] == pytest.approx(round(expected_hot(26.0, 50.0), 1))


def test_cold_case_applied_when_t_le_10_and_wind_gt_4_8(calc):
    df = pd.DataFrame(
        {
            "pred_tmed": [10.0],
            "pred_hrMedia": [40.0],
            "pred_velmedia": [4.9],
        }
    )
    out = calc.calculate_apparent_temp(df)

    exp = round(expected_cold(10.0, 4.9), 1)
    assert out.iloc[0] == pytest.approx(exp)


def test_cold_boundary_wind_equal_4_8_not_applied(calc):
    df = pd.DataFrame(
        {
            "pred_tmed": [10.0],
            "pred_hrMedia": [40.0],
            "pred_velmedia": [4.8],
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
    df = pd.DataFrame(
        {
            "pred_tmed": [20.0],
            "pred_hrMedia": [60.0],
            "pred_velmedia": [5.0],
        }
    )
    out = calc.calculate_apparent_temp(df)

    exp = round(expected_mid(20.0, 60.0, 5.0), 1)
    assert out.iloc[0] == pytest.approx(exp)


def test_mid_boundaries_not_inclusive(calc):
    # t == 10 => no mid
    df1 = pd.DataFrame(
        {"pred_tmed": [10.0], "pred_hrMedia": [60.0], "pred_velmedia": [0.0]}
    )
    out1 = calc.calculate_apparent_temp(df1)
    assert out1.iloc[0] == pytest.approx(10.0)

    # t == 26 => hot (sí)
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
            "pred_velmedia": [10.0, 5.0, 1.0, 4.8],  # last row: boundary no cold
        }
    )

    out = calc.calculate_apparent_temp(df)

    exp0 = round(expected_cold(5.0, 10.0), 1)  # cold (t<=10 & v>4.8)
    exp1 = round(expected_mid(20.0, 60.0, 5.0), 1)  # mid
    exp2 = round(expected_hot(30.0, 70.0), 1)  # hot
    exp3 = 10.0  # t=10, v=4.8 => base temp

    expected = pd.Series([exp0, exp1, exp2, exp3], name="pred_windchill")

    assert_series_equal(out.reset_index(drop=True), expected)


def test_input_dataframe_not_modified(calc):
    df = pd.DataFrame(
        {
            "pred_tmed": [20.0],
            "pred_hrMedia": [60.0],
            "pred_velmedia": [5.0],
        }
    )
    df_before = df.copy(deep=True)

    _ = calc.calculate_apparent_temp(df)

    assert list(df.columns) == list(df_before.columns)
    assert df.equals(df_before)
