from pydantic import ValidationError
import pytest

from src.schemas.weather import WeatherRecord


def test_valid_weather_record():
    data = {
        "fecha": "2024-01-01",
        "indicativo": "0076",
        "nombre": "Barcelona",
        "provincia": "Barcelona",
        "tmed": 15.5,
        "prec": "0,0",  # String español
    }
    record = WeatherRecord(**data)
    assert record.tmed == 15.5
    assert record.prec == 0.0  # Debe convertir la coma a float


def test_ip_precipitation():
    # "Ip" significa Inapreciable -> debe ser 0.0
    data = {
        "fecha": "2024-01-01",
        "indicativo": "TEST",
        "nombre": "Test",
        "provincia": "Test",
        "prec": "Ip",
    }
    record = WeatherRecord(**data)
    assert record.prec == 0.0


def test_invalid_date():
    data = {
        "fecha": "not-a-date",
        "indicativo": "TEST",
        "nombre": "Test",
        "provincia": "Test",
    }
    with pytest.raises(ValidationError):
        WeatherRecord(**data)
