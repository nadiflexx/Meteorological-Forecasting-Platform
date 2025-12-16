"""
PIPELINE 03: MODEL TRAINING
---------------------------
Orchestrates training and forecasting.
"""

from collections.abc import Iterable
from functools import reduce

import pandas as pd

from src.config.settings import Paths
from src.modeling.rainbow import RainbowCalculator
from src.modeling.trainers.atmosphere import AtmosphereModel
from src.modeling.trainers.rain import RainClassifier
from src.modeling.trainers.temperature import TemperatureModel
from src.utils.logger import log


def consolidate_results(dfs, on_keys: Iterable[str] | None = None):
    if on_keys is None:
        on_keys = ["fecha", "indicativo"]
    return reduce(
        lambda left, right: pd.merge(left, right, on=on_keys, how="inner"), dfs
    )


def main():
    data_file = Paths.PROCESSED / "weather_dataset_clean.csv"

    if not data_file.exists():
        log.error(f"❌ Dataset not found: {data_file}")
        return

    log.info("🌈 STARTING TRAINING PIPELINE 🌈")

    # 1. Train Models
    log.info("☔ TRAINING: Rain Classifier...")
    res_rain = RainClassifier(data_file).run_training()

    log.info("☀️ TRAINING: Atmosphere (Direct Humidity, Solar)...")
    res_atmos = AtmosphereModel(data_file).run_training()

    log.info("🌡️ TRAINING: Temperature...")
    res_temp = TemperatureModel(data_file).run_training()

    # 2. Fusion
    log.info("🔗 FUSION: Merging predictions...")
    full_preds = consolidate_results([res_rain, res_atmos, res_temp])

    # 3. Rainbow Logic
    log.info("🌈 LOGIC: Calculating Rainbow Probabilities...")
    calculator = RainbowCalculator()
    # Calculates 'rainbow_prob' based on preds
    final_results = calculator.calculate_probability(full_preds)

    # 4. Export
    cols_to_keep = [
        "fecha",
        "indicativo",
        "rainbow_prob",
        "prob_rain",
        "is_raining",
        "pred_sol",
        "pred_hrMedia",
        "pred_velmedia",
        "pred_tmed",
        "pred_tmax",
        "pred_tmin",
    ]

    # --- CORRECCIÓN DEL MERGE ---
    # Unimos usando SOLO las claves primarias (fecha, indicativo).
    # 'final_results' ya tiene las probabilidades calculadas.
    # 'full_preds' tiene las predicciones físicas (tmed, tmax, etc).
    final_df = pd.merge(
        final_results,
        full_preds,
        on=["fecha", "indicativo"],  # <--- ÚNICAS CLAVES VÁLIDAS
        how="left",
        suffixes=("", "_dup"),  # Por seguridad si hubiera duplicados
    )

    # Limpiamos columnas duplicadas si las hubiera
    final_df = final_df.loc[:, ~final_df.columns.str.endswith("_dup")]

    # Filtramos columnas finales
    valid_cols = [c for c in cols_to_keep if c in final_df.columns]

    output_path = Paths.PREDICTIONS / "rainbow_forecast_final.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    final_df[valid_cols].to_csv(output_path, index=False)

    log.info(f"💾 Saved to: {output_path}")

    # Preview
    cols_prev = [
        "fecha",
        "indicativo",
        "rainbow_prob",
        "prob_rain",
        "pred_sol",
        "pred_hrMedia",
    ]
    # Aseguramos que existan para el print
    cols_prev = [c for c in cols_prev if c in final_df.columns]

    print("\n🌈 TOP 10 RAINBOW DAYS (TEST SET):")
    print(final_df.sort_values("rainbow_prob", ascending=False).head(10)[cols_prev])


if __name__ == "__main__":
    main()
