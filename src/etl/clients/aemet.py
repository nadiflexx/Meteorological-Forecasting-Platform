"""
AEMET API Client.
Handles connection to AEMET OpenData API using Connection Pooling.
"""

import time
from typing import Any

import requests

from src.config.settings import APIs
from src.utils.logger import log


class AemetClient:
    def __init__(self):
        self.headers = {"api_key": APIs.AEMET_KEY, "Accept": "application/json"}
        # PROFESSIONAL TIP: Use a Session for connection pooling (Keep-Alive)
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _format_date(self, date_obj):
        return date_obj.strftime("%Y-%m-%dT%H:%M:%SUTC").replace(":", "%3A")

    def _download_final_json(self, url: str) -> list[dict[str, Any]] | None:
        try:
            time.sleep(0.2)  # Courteous delay
            # Use session here too
            res = self.session.get(url, timeout=APIs.TIMEOUT)

            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            log.warning(f"⚠️ Download error: {e}")
            return None

    def fetch_data_chunk(self, start_date, end_date, station_code) -> list[dict] | None:
        str_ini = self._format_date(start_date)
        end_date_full = end_date.replace(hour=23, minute=59, second=59)
        str_fin = self._format_date(end_date_full)

        endpoint = f"{APIs.AEMET_URL}/fechaini/{str_ini}/fechafin/{str_fin}/estacion/{station_code}"

        # No loop here. The loop is handled by the resilience utility.
        # This function simply TRIES once and reports result/error.
        try:
            response = self.session.get(endpoint, timeout=APIs.TIMEOUT)

            if response.status_code == 200:
                data_res = response.json()
                status = int(data_res.get("estado", 0))

                if status == 200:
                    return self._download_final_json(data_res["datos"])
                elif status == 404:
                    log.info(f"ℹ️ No Data: {station_code} ({start_date.date()})")
                    return None
                else:
                    log.error(f"❌ Logical Error: {data_res.get('descripcion')}")
                    return None

            elif response.status_code == 429:
                log.warning("⛔ Rate Limit (429).")
                raise ConnectionError(
                    "Rate Limit Hit"
                )  # Raise to trigger external retry

            else:
                log.error(f"❌ HTTP {response.status_code}")
                return None

        except Exception as e:
            # Re-raise to let the resilience utility handle the retry logic
            raise e
