"""
PIPELINE 03: MODEL TRAINING
----------------------------------------
Orchestrates training and forecasting of rain, atmosphere, and temperature models,
merging their predictions and applying rainbow probability calculations.
"""

from collections.abc import Iterable
from functools import reduce

import pandas as pd

from src.config.settings import FileNames, Paths
from src.modeling.rainbow import RainbowCalculator
from src.modeling.trainers.atmosphere import AtmosphereModel
from src.modeling.trainers.rain import RainClassifier
from src.modeling.trainers.temperature import TemperatureModel
from src.modeling.wind_chill import WindChillCalculator
from src.utils.logger import log


def consolidate_results(dfs, on_keys: Iterable[str] | None = None):
    """Merge a list of DataFrames on specified keys using an outer join."""
    if on_keys is None:
        on_keys = ["fecha", "indicativo"]
    return reduce(
        lambda left, right: pd.merge(left, right, on=on_keys, how="outer"), dfs
    )


def main():
    """Main function to run the training pipeline.
    Checks for the existence of the processed dataset, trains individual models,
    consolidates their predictions, applies rainbow logic, and saves the final results."""
    data_file = Paths.PROCESSED / FileNames.CLEAN_DATA

    if not data_file.exists():
        log.error(f"❌ Dataset not found: {data_file}")
        return

    log.info("🌈 STARTING TRAINING PIPELINE 🌈")

    # 1. Train Models
    log.info("☔ TRAINING: Rain Classifier...")
    res_rain = RainClassifier(data_file).run_training()

    log.info("☀️ TRAINING: Atmosphere...")
    res_atmos = AtmosphereModel(data_file).run_training()

    log.info("🌡️ TRAINING: Temperature...")
    res_temp = TemperatureModel(data_file).run_training()

    # 2. Fusion
    log.info("🔗 FUSION: Merging predictions...")
    full_preds = consolidate_results([res_rain, res_atmos, res_temp])

    # 3. Rainbow Logic
    log.info("🌈 LOGIC: Calculating Rainbow Probabilities...")
    calculator = RainbowCalculator()
    final_results = calculator.calculate_probability(full_preds)

    # 4. Wind Chill Logic
    log.info("👕​ LOGIC: Calculating Wind Chill Prediction...")
    WindChill_calculator = WindChillCalculator()
    final_results['pred_windchill'] = WindChill_calculator.calculate_apparent_temp(full_preds)

    # 5. Load original data
    log.info("📂 Loading original data...")
    df_original = pd.read_csv(data_file)
    df_original["fecha"] = pd.to_datetime(df_original["fecha"])

    # 6. Export
    output_path = Paths.PREDICTIONS / FileNames.FORECAST_FINAL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_results.to_csv(output_path, index=False)

    log.info(f"💾 Saved to: {output_path}")


if __name__ == "__main__":
    main()
