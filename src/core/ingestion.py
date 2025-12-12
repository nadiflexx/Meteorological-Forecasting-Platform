import json
import re

from src.config import settings
from src.utils.logger import log


class DataIngestion:
    def __init__(self):
        if not settings.DATA_RAW_DIR.exists():
            settings.DATA_RAW_DIR.mkdir(parents=True)

    def _sanitize_name(self, name):
        """Limpieza de nombres de carpeta"""
        clean = re.sub(r"[^\w\s-]", "", name)
        clean = re.sub(r"[\s]+", "_", clean)
        return clean

    def _get_station_year_folder(self, station_code, station_name, year):
        clean_name = self._sanitize_name(station_name)
        folder_name = f"Station_{station_code}_{clean_name}"

        station_path = settings.DATA_RAW_DIR / folder_name
        if not station_path.exists():
            station_path.mkdir()

        year_path = station_path / str(year)
        if not year_path.exists():
            year_path.mkdir()

        return year_path

    def save_partial_data(self, data, start_date, end_date, station_code, station_name):
        year = start_date.year
        folder = self._get_station_year_folder(station_code, station_name, year)

        filename = (
            f"part_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        )
        filepath = folder / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        log.info(f"💾 Guardado parcial: {filename}")

    def consolidate_year(self, year, station_code, station_name):
        """
        Une los parciales, guarda el anual y BORRA los parciales.
        """
        folder = self._get_station_year_folder(station_code, station_name, year)

        if not folder.exists():
            return

        # 1. Identificar archivos
        files = sorted(folder.glob("part_*.json"))

        if not files:
            return

        log.info(
            f"🔄 Consolidando {len(files)} archivos para {station_name} ({year})..."
        )

        all_records = []
        files_processed = []  # Lista para rastrear qué borrar luego

        # 2. Leer y Unificar
        for file in files:
            try:
                with open(file, encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        all_records.extend(content)
                        files_processed.append(
                            file
                        )  # Marcamos para borrar solo si se leyó bien
            except Exception as e:
                log.error(f"Error leyendo {file.name}: {e}")

        if not all_records:
            log.warning(f"No se encontraron registros válidos para {year}.")
            return

        # 3. Guardar archivo final Consolidado
        final_filename = f"data_{year}.json"
        final_path = folder / final_filename

        try:
            with open(final_path, "w", encoding="utf-8") as f:
                json.dump(all_records, f, ensure_ascii=False, indent=4)
            log.info(
                f"✨ CONSOLIDADO GUARDADO: {final_filename} ({len(all_records)} registros)"
            )

            # 4. FASE DE LIMPIEZA (Solo si el guardado fue exitoso)
            log.info(f"🗑️ Eliminando archivos parciales del año {year}...")
            for p_file in files_processed:
                try:
                    p_file.unlink()  # Borrado físico del archivo
                except Exception as e:
                    log.error(f"No se pudo borrar {p_file.name}: {e}")

        except Exception as e:
            log.error(f"❌ Error crítico guardando consolidado {final_filename}: {e}")
            log.warning("⚠️ Se conservan los archivos parciales por seguridad.")
