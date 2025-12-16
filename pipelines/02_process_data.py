"""
PIPELINE 02: DATA PROCESSING
----------------------------
Cleans raw JSONs, merges with Open-Meteo physics data, handles missing values,
and generates the final 'weather_dataset_clean.csv'.
"""

from src.etl.processing import WeatherProcessor
from src.utils.logger import log


def run_processing_pipeline():
    """
    Executes the cleaning and transformation pipeline:
    1. Load Raw JSONs & Validate (Pydantic).
    2. Filter Bad Stations (<85% coverage).
    3. Merge Physical Data (Open-Meteo: Solar, Pressure, Dew Point).
    4. Smart Imputation (Interpolation + Climatology).
    5. Export Clean CSV.
    """
    try:
        log.info("🤖 STARTING DATA PROCESSING PIPELINE")

        processor = WeatherProcessor()
        processor.execute()

        log.info("✅ Processing Pipeline finished successfully.")

    except Exception as e:
        log.critical(f"💀 Fatal Error during processing: {e}")
        raise e


if __name__ == "__main__":
    run_processing_pipeline()
