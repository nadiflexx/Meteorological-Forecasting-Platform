import logging
import sys

from src.config.settings import Paths


def setup_logger(name="rainbow_ai_predictor"):
    """
    Configures and initializes the centralized logging system.

    This function sets up a dual-channel logging strategy to ensure both
    real-time feedback and historical persistence of execution events.

    Configuration Details:
    1.  **Directory Check**: Ensures the `logs/` directory exists before writing.
    2.  **File Output**: Appends logs to `execution.log` for post-execution auditing.
    3.  **Console Output**: Streams logs to `sys.stdout` for immediate monitoring.
    4.  **Formatting**: Standardizes messages with timestamps and severity levels
        (e.g., `2023-10-27 10:00:00 [INFO] Message`).

    Args:
        name (str): The name of the logger instance. Defaults to "rainbow_ai_predictor".

    Returns:
        logging.Logger: The configured logger object ready for use.
    """
    if not Paths.LOGS.exists():
        Paths.LOGS.mkdir(parents=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(Paths.LOGS / "execution.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


log = setup_logger()
