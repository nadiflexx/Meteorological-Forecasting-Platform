import pandas as pd

from src.modeling.rainbow import RainbowCalculator


def test_rainbow_logic_ideal_conditions():
    df = pd.DataFrame(
        {
            "fecha": ["2024-01-01"],
            "indicativo": ["A1"],
            "prob_rain": [0.70],
            "is_raining": [1],
            "pred_sol": [6.0],
            "pred_hrMedia": [90.0],
        }
    )

    calc = RainbowCalculator()
    result = calc.calculate_probability(df)

    assert result["rainbow_prob"].iloc[0] > 50.0


def test_rainbow_logic_no_sun():
    df = pd.DataFrame(
        {
            "fecha": ["2024-01-01"],
            "indicativo": ["A1"],
            "prob_rain": [0.90],
            "is_raining": [1],
            "pred_sol": [0.0],  # Sin sol
            "pred_hrMedia": [90.0],
        }
    )

    calc = RainbowCalculator()
    result = calc.calculate_probability(df)

    assert result["rainbow_prob"].iloc[0] == 0.0
