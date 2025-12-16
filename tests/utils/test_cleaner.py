from unittest.mock import MagicMock, call, patch

from src.utils.cleaner import run_cleaner


@patch("src.utils.cleaner.shutil")  # Mockeamos shutil para verificar el borrado
@patch("src.utils.cleaner.Paths")  # Mockeamos Paths para simular carpetas
def test_run_cleaner_logic(mock_paths, mock_shutil):
    # --- 1. PREPARAR ESCENARIO ---

    # Simular Paths.RAW
    mock_raw = MagicMock()
    mock_paths.RAW = mock_raw
    mock_raw.exists.return_value = True

    # Simular una carpeta de Estación
    mock_station = MagicMock()
    mock_station.is_dir.return_value = True
    mock_station.name = "Station_Test"

    # Simular Año VACÍO (Debe borrarse)
    year_empty = MagicMock()
    year_empty.is_dir.return_value = True
    year_empty.name = "2020"
    year_empty.glob.return_value = []  # No encuentra JSONs

    # Simular Año LLENO (No debe borrarse)
    year_full = MagicMock()
    year_full.is_dir.return_value = True
    year_full.name = "2021"
    year_full.glob.return_value = ["data.json"]  # Encuentra JSONs

    # Configurar la estructura de directorios
    # RAW contiene la estación
    mock_raw.iterdir.return_value = [mock_station]
    # La estación contiene los años
    mock_station.iterdir.return_value = [year_empty, year_full]

    # --- 2. EJECUTAR ---
    run_cleaner()

    # --- 3. VALIDAR ---

    # Verificar que se llamó a rmtree con la carpeta vacía
    mock_shutil.rmtree.assert_any_call(year_empty)

    # Verificar que NO se llamó a rmtree con la carpeta llena
    # Obtenemos lista de argumentos de todas las llamadas a rmtree
    calls = mock_shutil.rmtree.call_args_list
    assert call(year_full) not in calls, "No se debería borrar el año con datos"
