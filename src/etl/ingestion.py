"""
Data Ingestion Logic.

Manages the lifecycle of persistent storage for raw data, handling
atomic writes of partial batches and their eventual consolidation
into unified yearly datasets.
"""

import json
import os
import re

from src.config.settings import Paths
from src.utils.logger import log


class DataIngestion:
    """
    Handles file system operations for the ETL Ingestion phase.

    This class ensures that data downloaded in chunks is safely stored
    to disk immediately (to prevent data loss on crash) and later
    merged into a clean, chronological structure.
    """

    def __init__(self):
        if not Paths.RAW.exists():
            Paths.RAW.mkdir(parents=True)

    def _sanitize_name(self, name):
        """
        Sanitizes strings to be filesystem-safe.
        Removes special characters and replaces spaces with underscores.
        """
        clean = re.sub(r"[^\w\s-]", "", name)
        clean = re.sub(r"[\s]+", "_", clean)
        return clean

    def _get_station_year_folder(self, station_code, station_name, year):
        """
        Generates and creates the hierarchical directory path.
        Structure: data/raw/Station_{ID}_{Name}/{Year}/
        """
        clean_name = self._sanitize_name(station_name)
        folder_name = f"Station_{station_code}_{clean_name}"

        station_path = Paths.RAW / folder_name
        if not station_path.exists():
            station_path.mkdir()

        year_path = station_path / str(year)
        if not year_path.exists():
            year_path.mkdir()

        return year_path

    def save_partial_data(self, data, start_date, end_date, station_code, station_name):
        """
        Writes a partial batch of data to disk (JSON).

        It uses `os.fsync` to ensure physical write durability, preventing
        data corruption in case of sudden system failure or interruption.

        Args:
            data (list): List of dictionary records.
            start_date (datetime): Start of the batch.
            end_date (datetime): End of the batch.
            station_code (str): Unique station ID.
            station_name (str): Human-readable name.
        """
        year = start_date.year
        folder = self._get_station_year_folder(station_code, station_name, year)

        filename = (
            f"part_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        )
        filepath = folder / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())

        log.info(f"💾 Saved partial: {filename}")

    def consolidate_year(self, year, station_code, station_name):
        """
        Merges all partial JSON fragments for a specific year into a single master file.

        Key operations:
        1. Reads all `part_*.json` files.
        2. Deduplicates records based on date.
        3. Sorts records chronologically.
        4. Saves the result as `data_{year}.json`.
        5. Deletes the temporary partial files.

        Args:
            year (int): The year to consolidate.
            station_code (str): Station ID.
            station_name (str): Station Name.
        """
        folder = self._get_station_year_folder(station_code, station_name, year)

        if not folder.exists():
            return

        files = sorted(folder.glob("part_*.json"))

        if not files:
            return

        log.info(f"🔄 Consolidating {len(files)} files for {station_name} ({year})...")

        all_records = []
        files_processed = []

        for file in files:
            try:
                with open(file, encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        all_records.extend(content)
                        files_processed.append(file)
            except Exception as e:
                log.error(f"Error reading {file.name}: {e}")

        if not all_records:
            return

        # 1. REMOVE DUPLICATES
        unique_records = {item["fecha"]: item for item in all_records}
        cleaned_list = list(unique_records.values())

        # 2. SORT BY DATE
        cleaned_list.sort(key=lambda x: x["fecha"])

        # 3. Save Final File
        final_filename = f"data_{year}.json"
        final_path = folder / final_filename

        try:
            with open(final_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_list, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())

            log.info(
                f"✨ CONSOLIDATED: {final_filename} ({len(cleaned_list)} ordered days)"
            )

            # 4. Cleanup
            for p_file in files_processed:
                try:
                    p_file.unlink()
                except Exception as e:
                    log.error(f"Could not delete {p_file.name}: {e}")

        except Exception as e:
            log.error(f"❌ Error saving consolidated file: {e}")
