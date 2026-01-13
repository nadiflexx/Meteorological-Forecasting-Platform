"""
AEMET API Client.

Manages the HTTP interface with the Spanish State Meteorological Agency (AEMET) OpenData API.
It implements Connection Pooling for performance and handles the specific two-step
request mechanism required by AEMET.
"""

import time
from typing import Any

import requests

from src.config.settings import APIs
from src.utils.logger import log


class AemetClient:
    """
    Wrapper class for AEMET OpenData.

    Features:
    - **Connection Pooling**: Uses `requests.Session` to reuse TCP connections,
      significantly reducing latency during sequential requests.
    - **Header Management**: Automatically injects the API Key into every request.
    """

    def __init__(self):
        self.headers = {"api_key": APIs.AEMET_KEY, "Accept": "application/json"}
        # Use a Session for connection pooling (Keep-Alive)
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _format_date(self, date_obj):
        """
        Formats datetime objects to AEMET's specific ISO-8601 requirement.
        Example: 2023-01-01T00:00:00UTC (with colon encoded as %3A)
        """
        return date_obj.strftime("%Y-%m-%dT%H:%M:%SUTC").replace(":", "%3A")

    def fetch_data_chunk(self, start_date, end_date, station_code) -> list[dict] | None:
        """
        Step 1 of AEMET Protocol: Request data for a specific time window and station.

        This function performs the initial query. If successful, it automatically
        triggers `_download_final_json`.

        Args:
            start_date (datetime): Start of the period.
            end_date (datetime): End of the period.
            station_code (str): AEMET Station ID (e.g., '0201D').

        Returns:
            list[dict] | None: The weather records if successful, None otherwise.

        Raises:
            ConnectionError: If a 429 (Rate Limit) is detected. This signal is
                             caught by the external resilience wrapper to trigger a backoff.
            Exception: For other network errors, allowing the wrapper to handle retries.
        """
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

    def _download_final_json(self, url: str) -> list[dict[str, Any]] | None:
        """
        Step 2 of AEMET Protocol: Download data from the temporary URL.

        The AEMET API first returns a metadata object containing a 'datos' URL.
        This method performs the actual GET request to that temporary URL to
        retrieve the JSON payload.
        """
        try:
            time.sleep(0.2)
            res = self.session.get(url, timeout=APIs.TIMEOUT)

            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            log.warning(f"⚠️ Download error: {e}")
            return None
