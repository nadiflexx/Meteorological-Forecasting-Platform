"""
Open-Meteo API Client.

Handles interaction with the Open-Meteo Historical Archive API to retrieve
physics-based meteorological data (Solar radiation, Pressure, Dew Point)
that serves to enrich the primary AEMET dataset.
"""

from datetime import datetime
import time
from typing import Any

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from src.config.settings import APIs
from src.utils.logger import log


class OpenMeteoClient:
    """
    Client wrapper for fetching historical weather reanalysis data.

    This class abstracts the complexity of the Open-Meteo API, handling:
    1. Caching (to reduce API load and speed up development).
    2. Automatic Retries (exponential backoff).
    3. Parsing binary/numpy responses into Pandas DataFrames.
    """

    def __init__(self):
        # Persistent caching to avoid redundant API calls
        cache_session = requests_cache.CachedSession(".cache", expire_after=-1)

        # Retry logic for resilience
        retry_session = retry(cache_session, retries=5, backoff_factor=1)

        self.client = openmeteo_requests.Client(session=retry_session)
        self.base_url = APIs.OPENMETEO_URL

    def fetch_solar_data(
        self, lat: float, lon: float, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Retrieves daily weather variables including Solar Radiation, Pressure, and Clouds.

        Args:
            lat (float): Latitude of the station.
            lon (float): Longitude of the station.
            start_date (datetime): Query start date.
            end_date (datetime): Query end date.

        Returns:
            pd.DataFrame: DataFrame with standardized columns [fecha, sol, om_prec, presion, nubes]
                          Returns an empty DataFrame if the request fails or dates are invalid.
        """
        today = datetime.now()

        if start_date > today:
            return pd.DataFrame()

        # Clamp end date to today if it's in the future
        request_end = today if end_date > today else end_date

        # Variables to request
        daily_vars = [
            "sunshine_duration",
            "precipitation_sum",
            "pressure_msl_mean",
            "cloud_cover_mean",
        ]

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": request_end.strftime("%Y-%m-%d"),
            "daily": daily_vars,
            "timezone": "auto",
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                responses = self.client.weather_api(self.base_url, params=params)
                response = responses[0]
                daily = response.Daily()

                # --- Extract Data ---
                data_dict: dict[str, Any] = {}

                # Map API response indices to our internal column names
                # 0: sunshine_duration (seconds -> hours)
                data_dict["sol"] = np.round(
                    daily.Variables(0).ValuesAsNumpy() / 3600.0, 2
                )

                # 1: precipitation_sum (mm)
                data_dict["om_prec"] = np.round(daily.Variables(1).ValuesAsNumpy(), 1)

                # 2: pressure_msl_mean (hPa)
                data_dict["presion"] = np.round(daily.Variables(2).ValuesAsNumpy(), 1)

                # 3: cloud_cover_mean (%)
                data_dict["nubes"] = np.round(daily.Variables(3).ValuesAsNumpy(), 0)

                # --- Handle Dates ---
                start_ts = daily.Time()
                end_ts = daily.TimeEnd()
                interval = daily.Interval()

                unix_times = np.arange(start_ts, end_ts, interval, dtype="int64")

                # Ensure all arrays have same length
                min_len = min(len(unix_times), len(data_dict["sol"]))
                unix_times = unix_times[:min_len]
                for k in data_dict:
                    data_dict[k] = data_dict[k][:min_len]

                # Convert to Datetime and adjust for Timezone shift
                ts_utc = pd.to_datetime(unix_times, unit="s", utc=True)
                ts_shifted = ts_utc + pd.Timedelta(hours=6)
                fechas = ts_shifted.tz_convert(None).normalize()

                df_res = pd.DataFrame(data_dict)
                df_res["fecha"] = fechas

                # Physical Constraints (Clips)
                df_res["sol"] = df_res["sol"].clip(lower=0.0)
                df_res["om_prec"] = df_res["om_prec"].clip(lower=0.0)
                df_res["nubes"] = df_res["nubes"].clip(0, 100)

                if not df_res.empty:
                    log.info(
                        f"      ☁️ Open-Meteo Fetched: {len(df_res)} days (Inc. Physics)"
                    )

                return df_res

            except Exception as e:
                error_msg = str(e).lower()
                if "limit exceeded" in error_msg:
                    wait_time = 65  # Open-Meteo minutely limit
                    if attempt < max_retries - 1:
                        log.warning(f"🛑 Rate limit hit. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                else:
                    log.error(f"❌ Open-Meteo Error: {e}")
                break

        return pd.DataFrame()
