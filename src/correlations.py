"""
Main entrypoint for the full data pipeline.

Steps:
1. Load multiple datasets
2. Merge and tag them
3. Analyse and aggregate
4. Visualize summaries
"""

from pathlib import Path

from utils.data_aggregator import DataAggregator
from utils.data_analysis import analyse_data
from utils.data_loaders import (
    load_data,
    safe_concat_dataframes,
    tag_df_with_metadata,
)
from utils.data_visualizers import DataVisualizer
from utils.enums import DataTypesEnum,  FileNamesEnum


def run_main():
    """Main script."""
    base_dir = Path(__file__).resolve().parents[1]
    data_dir = base_dir / "data" / "raw"
    df_2024 = list(data_dir.glob(f"{FileNamesEnum.METEOROLOGICAL}*.csv"))  

    print("🔍 Buscando CSV en:", data_dir)
    print("Archivos encontrados:", len(df_2024))

    # 1 Load datasets and Tag 
    df_list_2024 = []
    for files in df_2024:
        print(f"📂 Cargando: {files.name}")
        df = load_data(DataTypesEnum.CSV, path_to_data=files)
        df_list_2024.append(df)

    print(f"\n✅ Cargados y etiquetados {len(df_list_2024)} dataframes para 2024.")
    # 2️ Merge
    df_all = safe_concat_dataframes(df_list_2024)

    # 3 Analyse
    analysis = analyse_data(df_all)
    print("\n📊 BASIC STATS:")
    print(analysis["basic_stats"])

    print("\n🧩 COLUMN INFO:")
    print(analysis["column_info"])

    print("\n📈 NUMERIC SUMMARY:")
    print(analysis["numeric_summary"])

    print("\n📦 VALUE COUNTS:")
    print(analysis["value_counts"])

    # 4 Aggregate
    aggregator = DataAggregator(df_all)
    summary = aggregator.get_numeric_summary()
    print("\n📈 Numeric Summary:")
    print(summary)

    # 5 Visualize
    viz = DataVisualizer(df_all)
    viz.plot_correlation_matrix()
    viz.plot_by_category("city", "sales")
    viz.auto_visualize()


if __name__ == "__main__":
    run_main()