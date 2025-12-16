"""
PIPELINE 01: DATA INGESTION
---------------------------
Orchestrates the download of historical weather data.
Uses 'src.utils.resilience' to handle retries and network instability.
"""

from datetime import timedelta
import time

from dateutil.relativedelta import relativedelta

from src.config.settings import STATIONS, APIs, Paths, PipelineParams
from src.etl.clients.aemet import AemetClient
from src.etl.ingestion import DataIngestion
from src.utils.cleaner import run_cleaner
from src.utils.logger import log
from src.utils.resilience import fetch_with_retry_logic


def run_ingestion():
    log.info("🚀 STARTING INGESTION PIPELINE (ETL)")

    # Ensure environment is ready
    Paths.make_dirs()

    # Instantiate services
    client = AemetClient()
    ingestion = DataIngestion()

    # --- MAIN LOOP ---
    for code, name in STATIONS.items():
        log.info(f"📡 --- STATION: [{code}] {name} ---")

        current_date = PipelineParams.START_DATE
        processed_year = current_date.year

        while current_date < PipelineParams.END_DATE:
            # 1. Define Time Window (6 months)
            next_cycle_start = current_date + relativedelta(months=6)
            query_end = next_cycle_start - timedelta(days=1)

            if query_end > PipelineParams.END_DATE:
                query_end = PipelineParams.END_DATE

            # 2. Year Consolidation Check
            if current_date.year > processed_year:
                time.sleep(0.5)  # Allow FS to settle
                ingestion.consolidate_year(processed_year, code, name)
                processed_year = current_date.year

            # 3. API Call (Wrapped in Resilience Logic)
            # We pass the function and its arguments separately
            data = fetch_with_retry_logic(
                client.fetch_data_chunk,  # The function
                max_retries=APIs.RETRIES,  # Config
                start_date=current_date,  # Arg 1
                end_date=query_end,  # Arg 2
                station_code=code,  # Arg 3
            )

            # 4. Persistence
            if data:
                ingestion.save_partial_data(data, current_date, query_end, code, name)
            else:
                # If resilience returned empty, we log and move on (Gap in data)
                log.warning(
                    f"⚠️ Gap skipped: {current_date.date()} -> {query_end.date()}"
                )

            # 5. Advance Cursor
            current_date = next_cycle_start
            time.sleep(0.5)  # Rate limit courtesy

        # Final Cleanup for the station
        time.sleep(0.5)
        ingestion.consolidate_year(processed_year, code, name)

        log.info(f"✅ Station {name} completed.\n")
        time.sleep(1)

    log.info("💾 DOWNLOAD COMPLETED.")
    run_cleaner()


if __name__ == "__main__":
    try:
        run_ingestion()
    except KeyboardInterrupt:
        log.warning("🛑 Execution stopped by user.")
    except Exception as e:
        log.critical(f"💀 Fatal Error in Ingestion: {e}")
