import time

from src.config import settings
from src.core.api_client import AemetClient
from src.core.ingestion import DataIngestion
from src.utils.date_helper import get_next_period
from src.utils.logger import log


class WeatherPipeline:
    def __init__(self):
        self.client = AemetClient()
        self.ingestion = DataIngestion()

    def _process_single_station(self, code, name):
        """Procesa todo el historial para una sola estación"""
        current_date = settings.START_DATE
        processed_year = current_date.year

        log.info(f"📡 Iniciando descarga: [{code}] {name}")

        while current_date < settings.END_DATE:
            # Usamos la utilidad de fechas
            query_end_date, next_cycle_start = get_next_period(
                current_date, settings.END_DATE
            )

            # Consolidación anual si cambiamos de año
            if current_date.year > processed_year:
                self.ingestion.consolidate_year(processed_year, code, name)
                processed_year = current_date.year

            # Llamada API
            data = self.client.fetch_data_chunk(current_date, query_end_date, code)

            # Guardado
            if data:
                self.ingestion.save_partial_data(
                    data, current_date, query_end_date, code, name
                )

            # Avanzar
            current_date = next_cycle_start
            time.sleep(0.2)  # Micro pausa

        # Consolidación final al terminar la estación
        self.ingestion.consolidate_year(processed_year, code, name)
        log.info(f"✅ Finalizado: {name}")

    def run(self):
        """Punto de entrada para ejecutar todas las estaciones configuradas"""
        log.info("🚀 INICIANDO PIPELINE GLOBAL")

        total_stations = len(settings.STATIONS)

        for idx, (code, name) in enumerate(settings.STATIONS.items(), 1):
            log.info(f"--- Progreso: {idx}/{total_stations} ---")

            try:
                self._process_single_station(code, name)
            except Exception as e:
                log.error(f"❌ Error crítico procesando estación {name}: {e}")
                # Continuamos con la siguiente estación a pesar del error
                continue

            time.sleep(1)  # Pausa entre estaciones

        log.info("🏁 EJECUCIÓN DEL PIPELINE COMPLETADA")
