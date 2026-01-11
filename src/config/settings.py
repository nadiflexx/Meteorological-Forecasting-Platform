"""
Global Configuration Settings.
Single Source of Truth (SSOT) for the entire project.
"""

from datetime import datetime
import os
from pathlib import Path
from typing import Any, TypedDict

from dotenv import load_dotenv

# Load Environmental Variables
load_dotenv()


class Paths:
    """Centralized management of project file paths."""

    ROOT = Path(__file__).resolve().parent.parent.parent
    DATA = ROOT / "data"
    RAW = DATA / "raw"
    PROCESSED = DATA / "processed"
    PREDICTIONS = DATA / "predictions"
    PREDICTIONS_COMPARATION = PREDICTIONS / "predictions_comparation"
    MODEL_ANALYSIS = PREDICTIONS / "model_analysis"
    COMPARATIVE = PREDICTIONS / "comparative"
    TELEGRAM = DATA / "telegram"
    MODELS = ROOT / "models"
    LOGS = ROOT / "logs"
    APP = ROOT / "app"
    ASSETS = APP / "assets"
    PAGES = APP / "pages"

    @classmethod
    def make_dirs(cls):
        """Create necessary directories if they don't exist."""
        for path in [
            cls.RAW,
            cls.PROCESSED,
            cls.PREDICTIONS,
            cls.MODELS,
            cls.LOGS,
            cls.APP,
            cls.ASSETS,
            cls.MODEL_ANALYSIS,
            cls.PREDICTIONS_COMPARATION,
            cls.COMPARATIVE,
            cls.TELEGRAM,
        ]:
            path.mkdir(parents=True, exist_ok=True)


Paths.make_dirs()


class FileNames:
    """Centralized file names to avoid magic strings in code."""

    # Input Data
    CLEAN_DATA = "weather_dataset_clean.csv"

    # Outputs (Predictions)
    FORECAST_FINAL = "rainbow_forecast_final.csv"
    FORECAST_ONESTEP = "one_step_forecast_2025.csv"
    FORECAST_RECURSIVE = "recursive_forecast_2025.csv"

    # Models (Naming convention prefix)
    MODEL_PREFIX = "lgbm_"
    MODEL_RAIN = "lgbm_rain_classifier.pkl"

    # Analysis Reports
    FEATURE_IMPORTANCE = "feature_importance.png"
    COMPARATIVE_ANALYSIS = "comparative_analysis.png"
    CORRELATION_MATRIX = "analysis_correlation_matrix.png"

    SUBSCRIPTIONS_FILE = "telegram_subscriptions.json"
    RAINBOW = "01_rainbow_hunter.py"
    AUDIT = "02_model_audit.py"
    WEATHER = "03_weather_forecast.py"
    WINDCHILL = "04_wind_chill_notify_form.py"


class APIs:
    """External Service Configuration."""

    AEMET_KEY = os.getenv("AEMET_API_KEY")
    AEMET_URL = (
        "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
    )

    OPENMETEO_URL = "https://archive-api.open-meteo.com/v1/archive"

    # Client settings
    RETRY_DELAY = 70
    TIMEOUT = 30
    RETRIES = 5
    CACHE_EXPIRE = 3600


class PipelineParams:
    """ETL Data Engineering parameters."""

    START_YEAR = 2009
    START_DATE = datetime(2009, 1, 1)
    END_DATE = datetime(2025, 12, 31)


class ExperimentConfig:
    """Machine Learning Experiment Setup (Fechas de Corte)."""

    VAL_START_DATE = "2024-01-01"
    TEST_START_DATE = "2025-01-01"
    TARGET_YEAR = 2025


class FeatureConfig:
    """
    Feature Engineering Configuration.
    Ensures training and inference use exactly the same features.
    """

    # Columns to predict
    TARGETS: list[str] = ["tmed", "tmin", "tmax", "sol", "hrMedia", "velmedia", "rain"]

    # Columns to apply LAGS (Shift)
    LAG_COLS: list[str] = [
        "tmed",
        "tmin",
        "tmax",
        "presMin",
        "hrMedia",
        "presion",
        "nubes",
        "velmedia",
        "sol",
        "prec",
    ]

    # Lag periods (days back)
    LAGS: list[int] = [1, 2, 7]

    # Columns to apply ROLLING WINDOWS
    ROLL_COLS: list[str] = ["tmed", "hrMedia", "presion", "nubes"]

    # Rolling window sizes (days)
    WINDOWS: list[int] = [3, 7, 14]


class ModelConfig:
    """LightGBM Hyperparameters."""

    # Regression (Temperature, Atmosphere)
    LGBM_REGRESSION: dict[str, Any] = {
        "objective": "regression",
        "metric": "mae",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.9,
        "verbose": -1,
        "force_col_wise": True,
    }

    # Classification (Rain)
    LGBM_CLASSIFIER: dict[str, Any] = {
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        "num_leaves": 40,
        "learning_rate": 0.04,
        "feature_fraction": 0.8,
        "verbose": -1,
    }

    # Threshold to decide if it rains (0.0 to 1.0)
    RAIN_THRESHOLD = 0.3


class StationData(TypedDict):
    """Structure for meteorological station data."""

    lat: float
    lon: float
    name: str


STATIONS: dict[str, str] = {
    "0252D": "Arenys De Mar",
    "0106X": "Balsareny",
    "0201D": "Barcelona Port Olímpic",
    "0076": "Barcelona Aeropuerto",
    "0200E": "Barcelona, Fabra",
    "0201X": "Barcelona, Museo Marítimo",
    "0092X": "Berga",
    "0222X": "Caldes De Montbui",
    "0194D": "Corbera, Pic D'Agulles",
    "0260X": "Fogars De Montclús",
    "0171X": "Igualada",
    "0149X": "Manresa",
    "0149D": "Manresa (La Culla)",
    "0120X": "Moià",
    "0158X": "Monistrol De Montserrat",
    "0158O": "Montserrat",
    "0061X": "Pontons",
    "0114X": "Prats De Lluçanès",
    "0229I": "Sabadell Aeropuerto",
    "0349": "Sant Julià De Vilatorta",
    "0255B": "Santa Susanna",
    "0073X": "Sitges",
    "0341X": "Tona",
    "0341": "Tona (Escola)",
    "0066X": "Vilafranca Del Penedès",
    "0244X": "Vilassar De Dalt",
}

STATION_COORDS: dict[str, StationData] = {
    "0252D": {"lat": 41.581, "lon": 2.550, "name": "Arenys de Mar"},
    "0244X": {"lat": 41.517, "lon": 2.360, "name": "Vilassar de Dalt"},
    "0255B": {"lat": 41.637, "lon": 2.710, "name": "Santa Susanna"},
    "0073X": {"lat": 41.237, "lon": 1.807, "name": "Sitges"},
    "0201D": {"lat": 41.380, "lon": 2.170, "name": "Barcelona - Port Olímpic"},
    "0200E": {"lat": 41.418, "lon": 2.124, "name": "Barcelona - Fabra"},
    "0201X": {"lat": 41.376, "lon": 2.173, "name": "Barcelona - Museo Marítimo"},
    "0076": {"lat": 41.293, "lon": 2.070, "name": "Barcelona - Aeropuerto"},
    "0229I": {"lat": 41.520, "lon": 2.105, "name": "Sabadell - Aeropuerto"},
    "0194D": {"lat": 41.420, "lon": 1.920, "name": "Corbera - Pic D'Agulles"},
    "0149D": {"lat": 41.725, "lon": 1.826, "name": "Manresa - La Culla"},
    "0149X": {"lat": 41.720, "lon": 1.820, "name": "Manresa"},
    "0106X": {"lat": 41.863, "lon": 1.878, "name": "Balsareny"},
    "0158O": {"lat": 41.590, "lon": 1.830, "name": "Montserrat"},
    "0158X": {"lat": 41.610, "lon": 1.840, "name": "Monistrol de Montserrat"},
    "0120X": {"lat": 41.810, "lon": 2.095, "name": "Moià"},
    "0092X": {"lat": 42.100, "lon": 1.850, "name": "Berga"},
    "0114X": {"lat": 42.008, "lon": 2.030, "name": "Prats de Lluçanès"},
    "0341X": {"lat": 41.850, "lon": 2.227, "name": "Tona"},
    "0341": {"lat": 41.852, "lon": 2.225, "name": "Tona (Escola)"},
    "0349": {"lat": 41.923, "lon": 2.327, "name": "Sant Julià de Vilatorta"},
    "0260X": {"lat": 41.730, "lon": 2.440, "name": "Fogars de Montclús"},
    "0222X": {"lat": 41.633, "lon": 2.167, "name": "Caldes de Montbui"},
    "0171X": {"lat": 41.583, "lon": 1.617, "name": "Igualada"},
    "0066X": {"lat": 41.346, "lon": 1.698, "name": "Vilafranca del Penedès"},
    "0061X": {"lat": 41.415, "lon": 1.515, "name": "Pontons"},
}

VAR_META = {
    "tmed": {"label": "Mean Temperature", "unit": "°C", "color": "orange"},
    "tmin": {"label": "Minimum Temperature", "unit": "°C", "color": "blue"},
    "tmax": {"label": "Maximum Temperature", "unit": "°C", "color": "red"},
    "sol": {"label": "Hours of Sunlight", "unit": "h", "color": "gold"},
    "hrMedia": {"label": "Relative Humidity", "unit": "%", "color": "teal"},
    "velmedia": {"label": "Wind Speed", "unit": "km/h", "color": "purple"},
    "rain": {"label": "Rain Probability", "unit": "%", "color": "navy"},
}

SEASONS = {
    "Winter (Jan-Mar)": [1, 2, 3],
    "Spring (Apr-Jun)": [4, 5, 6],
    "Summer (Jul-Sep)": [7, 8, 9],
    "Autumn (Oct-Dec)": [10, 11, 12],
}

# App main image
HERO_IMAGE_URL = (
    "https://cdn.mos.cms.futurecdn.net/ZcS3oG3vjPb4mnVcRYGbmk.jpg.webp"
    "?q=80&w=2070&auto=format&fit=crop"
)

TELEGRAM_REDIRECT = "https://t.me/P3G3Bot"
