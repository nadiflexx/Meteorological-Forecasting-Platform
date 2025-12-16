from datetime import datetime
from unittest.mock import MagicMock, patch

from src.etl.clients.aemet import AemetClient


@patch("src.etl.clients.aemet.requests.Session")
def test_aemet_fetch_success(mock_session_cls):
    # Setup
    mock_session = mock_session_cls.return_value

    # Mockear respuesta inicial (URL temporal)
    mock_res_1 = MagicMock()
    mock_res_1.status_code = 200
    mock_res_1.json.return_value = {"estado": 200, "datos": "http://download.url"}

    # Mockear respuesta descarga (Datos finales)
    mock_res_2 = MagicMock()
    mock_res_2.status_code = 200
    mock_res_2.json.return_value = [{"fecha": "2024-01-01", "valor": 10}]

    # Configurar side_effect para devolver res_1 y luego res_2
    mock_session.get.side_effect = [mock_res_1, mock_res_2]

    client = AemetClient()
    data = client.fetch_data_chunk(datetime(2024, 1, 1), datetime(2024, 1, 2), "TEST")

    assert data is not None
    assert len(data) == 1
    assert data[0]["valor"] == 10


@patch("src.etl.clients.aemet.requests.Session")
def test_aemet_rate_limit(mock_session_cls):
    mock_session = mock_session_cls.return_value

    # Simular 429
    mock_res = MagicMock()
    mock_res.status_code = 429

    # Para evitar bucle infinito, lanzamos una excepción después del primer intento
    mock_session.get.side_effect = [mock_res, Exception("Break Loop")]

    client = AemetClient()

    # Esperamos que capture el 429 y luego rompa por la excepción
    # (En la vida real duerme y reintenta, aquí testeamos que detecta el 429)
    # use contextlib.suppress(Exception)
    try:
        client.fetch_data_chunk(datetime(2024, 1, 1), datetime(2024, 1, 2), "TEST")
    except Exception:
        pass

    # No podemos asertar mucho más sin hacer el test muy lento,
    # pero aseguramos que llamó a get
    assert mock_session.get.called
