from src.utils.cleaner import run_cleaner
from src.utils.logger import log


def main():
    try:
        # --- BLOQUE DE DESCARGA (COMENTADO) ---
        # log.info("Arrancando sistema de predicción...")
        # pipeline = WeatherPipeline()
        # pipeline.run()

        run_cleaner()
    except KeyboardInterrupt:
        log.warning("🛑 Ejecución detenida manualmente por el usuario.")
    except Exception as e:
        log.critical(f"💀 Error fatal en el sistema: {e}")


if __name__ == "__main__":
    main()
