from datetime import datetime
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Rutas Base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
LOG_DIR = BASE_DIR / "logs"

# Credenciales
API_KEY = os.getenv("AEMET_API_KEY")
if not API_KEY:
    raise ValueError("❌ CRÍTICO: Falta AEMET_API_KEY en el archivo .env")

# Configuración AEMET
AEMET_BASE_URL = (
    "https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos"
)

# LISTA DE ESTACIONES (Extraída de tu HTML)
STATIONS = {
    "0252D": "Arenys De Mar",
    "0106X": "Balsareny",
    "0201D": "Barcelona",
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

# Configuración del Pipeline
RETRY_DELAY_SECONDS = 70  # 1m 10s
REQUEST_TIMEOUT = 30
START_DATE = datetime(1950, 1, 1)
END_DATE = datetime(2025, 6, 6)
