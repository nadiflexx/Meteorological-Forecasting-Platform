from datetime import date

from pydantic import BaseModel, field_validator


class WeatherRecord(BaseModel):
    """
    Schema defining the structure of a valid meteorological record.

    This Pydantic model acts as a data contract, ensuring that raw data
    ingested from the API adheres to expected types. It includes custom
    logic to handle Spanish formatting quirks (e.g., decimal commas) automatically.
    """

    fecha: date
    indicativo: str
    nombre: str
    provincia: str
    altitud: str | None = None

    # Meteorological fields
    tmed: float | None = None
    prec: float | None = None
    tmin: float | None = None
    tmax: float | None = None
    dir: str | None = None
    velmedia: float | None = None
    racha: float | None = None
    sol: float | None = None
    presMax: float | None = None
    presMin: float | None = None
    hrMedia: float | None = None

    # --- AUTOMATIC VALIDATION & CLEANING ---

    @field_validator(
        "tmed",
        "prec",
        "tmin",
        "tmax",
        "velmedia",
        "racha",
        "sol",
        "presMax",
        "presMin",
        "hrMedia",
        mode="before",
    )
    @classmethod
    def parse_float_spanish(cls, v):
        """
        Converts Spanish numerical formats (e.g., "10,5", "Ip") to standard floats.

        The `mode='before'` argument ensures this method runs BEFORE Pydantic
        attempts its default validation. This allows us to intercept strings
        like "10,5" and convert them to floats before Pydantic raises a TypeError.

        Args:
            v: The raw value coming from the API (string, int, float, or None).

        Returns:
            float | None: The cleaned float value or None if parsing fails.
        """
        if v is None or v == "":
            return None

        if isinstance(v, (float, int)):
            return float(v)

        if isinstance(v, str):
            # Basic cleanup: Replace decimal comma with dot and remove spaces
            v_clean = v.replace(",", ".").strip()

            # Special Case: "Ip" means "Inappreciable" (trace amount of rain) -> 0.0
            if v_clean.lower() == "ip":
                return 0.0

            try:
                return float(v_clean)
            except ValueError:
                # If conversion fails (e.g., corrupt text), return None to avoid crashing the pipeline
                return None

        return None
