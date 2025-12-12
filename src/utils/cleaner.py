import shutil

from src.config import settings
from src.utils.logger import log


def run_cleaner():
    log.info("🧹 INICIANDO LIMPIEZA DE CARPETAS VACÍAS (HISTÓRICAS)")

    if not settings.DATA_RAW_DIR.exists():
        log.warning("⚠️ No existe el directorio de datos data/raw")
        return

    # 1. Obtener todas las carpetas de estaciones
    station_dirs = sorted([d for d in settings.DATA_RAW_DIR.iterdir() if d.is_dir()])

    for station_dir in station_dirs:
        log.info(f"🔎 Analizando estación: {station_dir.name}")

        # 2. Obtener carpetas de años ordenadas (Importante para borrar cronológicamente)
        # Filtramos solo si es numérico para evitar borrar cosas raras
        year_dirs = sorted(
            [d for d in station_dir.iterdir() if d.is_dir() and d.name.isdigit()],
            key=lambda x: int(x.name),
        )

        data_found_in_station = False

        for year_dir in year_dirs:
            # Si ya encontramos datos anteriormente en esta estación,
            # ASUMIMOS que el resto es válido y PARAMOS de borrar en esta estación.
            if data_found_in_station:
                break

            # 3. Verificar si hay JSONs dentro
            json_files = list(year_dir.glob("*.json"))

            if json_files:
                # ¡ENCONTRAMOS DATOS!
                log.info(
                    f"   ✅ Datos encontrados en {year_dir.name}. Se detiene la limpieza para esta estación."
                )
                data_found_in_station = True
            else:
                # ESTÁ VACÍA (O sin jsons): BORRAR
                try:
                    shutil.rmtree(year_dir)  # Borra la carpeta y lo que tenga dentro
                    log.info(f"   🗑️ Borrado año vacío: {year_dir.name}")
                except Exception as e:
                    log.error(f"   ❌ Error borrando {year_dir.name}: {e}")

        # 4. (Opcional) Si la estación quedó totalmente vacía (sin ningún año), borrar la estación
        if not any(station_dir.iterdir()):
            try:
                station_dir.rmdir()
                log.info(
                    f"   💀 Estación totalmente vacía eliminada: {station_dir.name}"
                )
            except:
                pass

    log.info("✨ LIMPIEZA COMPLETADA ✨")
