import time

import requests

from src.config import settings
from src.utils.logger import log


class AemetClient:
    def __init__(self):
        self.headers = {"api_key": settings.API_KEY, "Accept": "application/json"}

    def _format_date(self, date_obj):
        """Formatea fecha y codifica los dos puntos como %3A"""
        return date_obj.strftime("%Y-%m-%dT%H:%M:%SUTC").replace(":", "%3A")

    def _download_final_json(self, url):
        try:
            time.sleep(0.5)
            res = requests.get(url, timeout=settings.REQUEST_TIMEOUT)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception:
            return None

    def fetch_data_chunk(self, start_date, end_date, station_code):
        # 1. Formatear Inicio (Se queda en 00:00:00)
        str_ini = self._format_date(start_date)

        # 2. Formatear Fin (Forzamos las 23:59:59) <--- CAMBIO CLAVE AQUÍ
        # Creamos una copia de la fecha fin pero con la hora al final del día
        end_date_full_day = end_date.replace(hour=23, minute=59, second=59)
        str_fin = self._format_date(end_date_full_day)

        endpoint = f"{settings.AEMET_BASE_URL}/fechaini/{str_ini}/fechafin/{str_fin}/estacion/{station_code}"

        while True:
            try:
                response = requests.get(
                    endpoint, headers=self.headers, timeout=settings.REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    data_res = response.json()
                    status = data_res.get("estado")

                    if status == 200:
                        return self._download_final_json(data_res["datos"])
                    elif status == 404:
                        # Log nivel INFO (normal) en lugar de ERROR
                        log.info(
                            f"ℹ️ Sin datos en {station_code} ({start_date.date()} a {end_date.date()})."
                        )
                        return None
                    else:
                        log.error(
                            f"❌ API Lógico ({station_code}): {data_res.get('descripcion')}"
                        )

                elif response.status_code == 429:
                    log.warning("⛔ Límite API (429).")

                else:
                    log.error(
                        f"❌ HTTP Error {response.status_code} en estación {station_code}"
                    )

            except Exception as e:
                log.error(f"🔥 Error conexión: {e}")

            log.info(f"⏳ Esperando {settings.RETRY_DELAY_SECONDS}s para reintentar...")
            time.sleep(settings.RETRY_DELAY_SECONDS)
