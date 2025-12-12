import logging
import sys

from src.config.settings import LOG_DIR


def setup_logger(name="weather_ai"):
    # Crear carpeta de logs si no existe
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Formato del log: [FECHA] [NIVEL] Mensaje
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler 1: Archivo (guarda todo)
    file_handler = logging.FileHandler(LOG_DIR / "execution.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler 2: Consola (para ver en vivo)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Instancia global del logger
log = setup_logger()
