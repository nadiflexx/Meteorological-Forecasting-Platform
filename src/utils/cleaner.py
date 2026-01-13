import shutil

from src.config.settings import Paths
from src.utils.logger import log


def run_cleaner():
    """
    Performs a cleanup of the raw data directory structure.

    This utility ensures that the filesystem remains tidy by removing empty
    directories generated during initialization or interrupted ingestion phases.

    Operational Logic:
    1.  **Traversal**: Iterates through all Station folders in `data/raw`.
    2.  **Ordering**: Checks Year folders in ascending numerical order.
    3.  **Deletion**: Removes year folders that do not contain any `.json` files.
    4.  **Safety Stop**: As soon as a year folder *with* data is found, the process
        stops for that station. This assumes that once valid historical data starts,
        subsequent folders are intentional and should be preserved.
    5.  **Station Pruning**: If a station folder is left completely empty after
        the year cleanup, the station folder itself is removed.
    """
    log.info("🧹 STARTING EMPTY FOLDER CLEANUP (HISTORICAL)")

    if not Paths.RAW.exists():
        log.warning("⚠️ Data directory data/raw does not exist")
        return

    # 1. Get all station folders
    station_dirs = sorted([d for d in Paths.RAW.iterdir() if d.is_dir()])

    for station_dir in station_dirs:
        log.info(f"🔎 Analyzing station: {station_dir.name}")

        # 2. Ascending filter by year and only if its Numeric
        year_dirs = sorted(
            [d for d in station_dir.iterdir() if d.is_dir() and d.name.isdigit()],
            key=lambda x: int(x.name),
        )

        data_found_in_station = False

        for year_dir in year_dirs:
            # If data was found previously in this station, stop removing.
            # Assumption: Once valid data starts, subsequent folders are valid or pending.
            if data_found_in_station:
                break

            # 3. Verify if it contains JSON
            json_files = list(year_dir.glob("*.json"))

            if json_files:
                log.info(
                    f"   ✅ Data found in {year_dir.name}. Stopping cleanup for this station."
                )
                data_found_in_station = True
            else:
                # It is empty (DELETE)
                try:
                    shutil.rmtree(year_dir)
                    log.info(f"   🗑️ Deleted empty year: {year_dir.name}")
                except Exception as e:
                    log.error(f"   ❌ Error deleting {year_dir.name}: {e}")

        # 4. (Optional) If the station folder is completely empty, delete it
        if not any(station_dir.iterdir()):
            try:
                station_dir.rmdir()
                log.info(f"   💀 Fully empty station removed: {station_dir.name}")
            except Exception as e:
                log.error(f"   ❌ Error deleting station: {e}")
                pass

    log.info("✨ CLEANUP COMPLETED ✨")
