from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from src.etl.ingestion import DataIngestion


@patch("src.etl.ingestion.os.fsync")  # Mockear fsync (sistema operativo)
@patch("src.etl.ingestion.Paths")  # Mockear Paths
def test_save_partial_data(mock_paths, mock_fsync):
    # Setup mocks
    mock_raw = MagicMock()
    mock_paths.RAW = mock_raw
    mock_raw.exists.return_value = True  # RAW existe

    ingestion = DataIngestion()

    data = [{"id": 1}]
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    # Mockear open para no escribir ficheros reales
    with patch("builtins.open", mock_open()) as mock_file:
        ingestion.save_partial_data(data, start, end, "ST01", "Station Name")

        # Validar escritura
        mock_file.assert_called_once()
        # Verificar que se intentó escribir JSON
        handle = mock_file()
        assert handle.write.called
        # Verificar fsync (escritura atómica)
        mock_fsync.assert_called()


@patch("src.etl.ingestion.os.fsync")
@patch("src.etl.ingestion.Paths")
def test_consolidate_year(mock_paths, mock_fsync):
    mock_station_folder = MagicMock()
    mock_station_folder.exists.return_value = True

    # Mockear glob para encontrar archivos parciales
    mock_part1 = MagicMock()
    mock_part1.name = "part_1.json"

    mock_station_folder.glob.return_value = [mock_part1]

    # El truco para mockear _get_station_year_folder sin tocar privado
    # es mockear el atributo RAW y la navegación de paths
    mock_paths.RAW.__truediv__.return_value = MagicMock()  # Station folder
    mock_paths.RAW.__truediv__.return_value.__truediv__.return_value = (
        mock_station_folder  # Year folder
    )

    ingestion = DataIngestion()

    # Mockear lectura y escritura
    with patch(
        "builtins.open", mock_open(read_data='[{"fecha": "2024-01-01", "val": 1}]')
    ):
        ingestion.consolidate_year(2024, "ST01", "Station")

        # Validar que intentó borrar el parcial
        mock_part1.unlink.assert_called_once()
