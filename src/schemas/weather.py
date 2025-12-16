from datetime import date

from pydantic import BaseModel, field_validator


class WeatherRecord(BaseModel):
    """
    Esquema que define cómo debe ser un registro meteorológico válido.
    Pydantic se encargará de convertir los strings a números automáticamente.
    """

    fecha: date
    indicativo: str
    nombre: str
    provincia: str
    altitud: str | None = None  # A veces viene como string, no es vital para el cálculo

    # Campos meteorológicos (Pueden ser None si faltan ese día)
    tmed: float | None = None
    prec: float | None = None
    tmin: float | None = None
    tmax: float | None = None
    dir: str | None = None  # Dirección del viento (suele ser numérico o string)
    velmedia: float | None = None
    racha: float | None = None
    sol: float | None = None
    presMax: float | None = None
    presMin: float | None = None
    hrMedia: float | None = None

    # --- VALIDACIÓN Y LIMPIEZA AUTOMÁTICA ---

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
        Convierte formatos españoles ("10,5", "Ip") a float estándar.
        mode='before': Se ejecuta ANTES de que Pydantic intente verificar si es float.
        """
        if v is None or v == "":
            return None

        if isinstance(v, (float, int)):
            return float(v)

        if isinstance(v, str):
            # Limpieza básica
            v_clean = v.replace(",", ".").strip()

            # Caso especial Lluvia Inapreciable
            if v_clean.lower() == "ip":
                return 0.0

            try:
                return float(v_clean)
            except ValueError:
                # Si no se puede convertir (ej: texto corrupto), devolvemos None
                return None

        return None
