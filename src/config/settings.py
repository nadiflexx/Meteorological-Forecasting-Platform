"""
Global Configuration Settings.
Single Source of Truth (SSOT) for the entire project.
"""

from datetime import datetime
import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv

# Load Environmental Variables
load_dotenv()


class Paths:
    """Centralized management of project file paths."""

    # Resolve Project Root
    ROOT = Path(__file__).resolve().parent.parent.parent

    # Backend / Data Paths
    DATA = ROOT / "data"
    RAW = DATA / "raw"
    PROCESSED = DATA / "processed"
    PREDICTIONS = DATA / "predictions"

    # Model Artifacts
    MODELS = ROOT / "models"
    LOGS = ROOT / "logs"

    # Frontend / App Paths
    APP = ROOT / "app"
    ASSETS = APP / "assets"

    @classmethod
    def make_dirs(cls):
        """Creates critical directories if they don't exist."""
        for path in [cls.RAW, cls.PROCESSED, cls.PREDICTIONS, cls.MODELS, cls.LOGS]:
            path.mkdir(parents=True, exist_ok=True)


# Ejecutar creación de directorios al importar
Paths.make_dirs()


class APIs:
    """External Service Configuration."""

    # AEMET
    AEMET_KEY = os.getenv("AEMET_API_KEY")
    if not AEMET_KEY:
        # Warning en lugar de error fatal para que la App funcione (solo visualización)
        # aunque el pipeline de entrenamiento falle.
        print("⚠️ WARNING: AEMET_API_KEY not found in .env")

    AEMET_URL = (
        "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
    )

    # Open-Meteo
    OPENMETEO_URL = "https://archive-api.open-meteo.com/v1/archive"

    # Pipeline Throttling
    RETRY_DELAY = 70
    TIMEOUT = 30
    RETRIES = 5


class PipelineParams:
    """Data Engineering parameters."""

    START_YEAR = 2009
    START_DATE = datetime(2009, 1, 1)
    END_DATE = datetime(2025, 12, 31)


# --- BUSINESS LOGIC DATA (Station Metadata) ---


class StationData(TypedDict):
    lat: float
    lon: float
    name: str


# Main Dictionary: Code -> Legible name
STATIONS: dict[str, str] = {
    "0171X": "Igualada",
}

# Metada detailed (Used by  ETL and for App Map)
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

# App main image
HERO_IMAGE_URL = (
    "https://images.unsplash.com/photo-1508615070457-7baeba4003ab"
    "?q=80&w=2070&auto=format&fit=crop"
)
