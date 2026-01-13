from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from src.etl.ingestion import DataIngestion


@patch("src.etl.ingestion.os.fsync")
@patch("src.etl.ingestion.Paths")
def test_save_partial_data(mock_paths, mock_fsync):
    mock_raw = MagicMock()
    mock_paths.RAW = mock_raw
    mock_raw.exists.return_value = True

    ingestion = DataIngestion()

    data = [{"id": 1}]
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 2)

    with patch("builtins.open", mock_open()) as mock_file:
        ingestion.save_partial_data(data, start, end, "ST01", "Station Name")

        mock_file.assert_called_once()
        handle = mock_file()
        assert handle.write.called
        mock_fsync.assert_called()


@patch("src.etl.ingestion.os.fsync")
@patch("src.etl.ingestion.Paths")
def test_consolidate_year(mock_paths, mock_fsync):
    mock_station_folder = MagicMock()
    mock_station_folder.exists.return_value = True

    mock_part1 = MagicMock()
    mock_part1.name = "part_1.json"

    mock_station_folder.glob.return_value = [mock_part1]

    mock_paths.RAW.__truediv__.return_value = MagicMock()
    mock_paths.RAW.__truediv__.return_value.__truediv__.return_value = (
        mock_station_folder  # Year folder
    )

    ingestion = DataIngestion()

    with patch(
        "builtins.open", mock_open(read_data='[{"fecha": "2024-01-01", "val": 1}]')
    ):
        ingestion.consolidate_year(2024, "ST01", "Station")

        mock_part1.unlink.assert_called_once()
