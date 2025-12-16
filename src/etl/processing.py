"""
Data Processing Engine.

Handles the transformation of raw JSON data into a clean, physics-enriched dataset.
Core responsibilities:
1. Loading & Validation (Pydantic).
2. Data Fusion (AEMET + Open-Meteo).
3. Missing Value Imputation (Interpolation + Climatology).
"""

import json
import time

import numpy as np
import pandas as pd
from pydantic import ValidationError

from src.config.settings import STATION_COORDS, STATIONS, Paths, PipelineParams
from src.etl.clients.openmeteo import OpenMeteoClient
from src.schemas.weather import WeatherRecord
from src.utils.logger import log


class WeatherProcessor:
    def __init__(self):
        self.raw_dir = Paths.RAW
        self.processed_dir = Paths.PROCESSED
        self.min_coverage_ratio = 0.85

        # Use PipelineParams for global dates
        self.global_start = PipelineParams.START_DATE
        self.global_end = PipelineParams.END_DATE

        self.solar_client = OpenMeteoClient()

        # Ensure output directory exists
        Paths.make_dirs()

    def load_and_validate(self) -> pd.DataFrame:
        """
        Loads raw JSON files and validates schema using Pydantic.
        """
        log.info("📂 Loading and validating raw data...")
        valid_records = []
        files = list(self.raw_dir.rglob("*.json"))

        for file in files:
            if file.name.startswith("part_"):
                continue
            try:
                with open(file, encoding="utf-8") as f:
                    raw_data = json.load(f)

                if not isinstance(raw_data, list):
                    continue

                for item in raw_data:
                    try:
                        record = WeatherRecord(**item)
                        # Filter by start date
                        if record.fecha >= self.global_start.date():
                            valid_records.append(record.model_dump())
                    except ValidationError:
                        continue
            except Exception:
                continue

        if not valid_records:
            raise ValueError("No valid records found in raw data.")

        df = pd.DataFrame(valid_records)
        df["fecha"] = pd.to_datetime(df["fecha"])
        return df

    def filter_bad_stations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes stations with insufficient data coverage (<85%).
        """
        log.info("🛡️ Filtering incomplete stations...")

        total_days = (self.global_end - self.global_start).days
        counts = df.groupby("indicativo")["fecha"].nunique()
        ratios = counts / total_days

        valid_stations = ratios[ratios >= self.min_coverage_ratio].index.tolist()

        log.info(f"   ✅ Retained {len(valid_stations)} stations.")
        return df[df["indicativo"].isin(valid_stations)].copy()

    def process_stations_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Core logic: Merges AEMET data with Open-Meteo physics and handles imputation.
        """
        log.info("🧩 Merging Physics Data & Imputing Missing Values...")

        # Drop old/dirty columns to be replaced by Open-Meteo
        df = df.drop(columns=["presMin", "presMax", "sol"], errors="ignore")

        stations = df["indicativo"].unique()
        global_idx = pd.date_range(
            start=self.global_start, end=self.global_end, freq="D"
        )

        # Full list of continuous variables to impute
        cols_continuous = [
            "tmed",
            "tmin",
            "tmax",
            "hrMedia",
            "velmedia",
            "racha",
            "presion",
            "nubes",
            "sol",
        ]

        df_list = []

        for i, station_code in enumerate(stations):
            st_name = STATIONS.get(station_code, station_code)
            log.info(
                f"   Processing [{i + 1}/{len(stations)}] {st_name} ({station_code})..."
            )

            # 1. Prepare Station DataFrame
            df_station = df[df["indicativo"] == station_code].copy()
            df_station = df_station.sort_values("fecha").drop_duplicates(
                subset=["fecha"]
            )
            df_station["fecha"] = pd.to_datetime(df_station["fecha"])

            # 2. Reindex to Global Calendar (Creates NaNs for missing days)
            df_station = df_station.set_index("fecha").reindex(global_idx)
            df_station["fecha"] = df_station.index
            df_station["indicativo"] = station_code

            # Fill static metadata
            for col in ["nombre", "provincia", "altitud"]:
                if col in df_station.columns:
                    df_station[col] = df_station[col].ffill().bfill()

            # 3. Fetch & Merge Open-Meteo Data
            coords = STATION_COORDS.get(station_code)

            # Initialize columns as NaN
            new_cols = ["sol", "presion", "nubes", "om_prec"]
            for c in new_cols:
                df_station[c] = np.nan

            if coords:
                df_om = self.solar_client.fetch_solar_data(
                    lat=coords["lat"],
                    lon=coords["lon"],
                    start_date=self.global_start,
                    end_date=self.global_end,
                )

                if not df_om.empty:
                    # Drop NaN placeholders
                    df_station = df_station.drop(columns=new_cols, errors="ignore")

                    # Merge on Date
                    df_station = pd.merge(
                        df_station,
                        df_om[["fecha"] + new_cols],
                        on="fecha",
                        how="left",
                    )
                time.sleep(0.5)  # Polite delay

            # 4. Hybrid Rain Imputation
            # Use Open-Meteo rain ('om_prec') to fill AEMET gaps
            if "prec" in df_station.columns:
                df_station["prec"] = df_station["prec"].fillna(df_station["om_prec"])
            else:
                df_station["prec"] = df_station["om_prec"]

            df_station = df_station.drop(columns=["om_prec"], errors="ignore")

            # 5. Advanced Imputation & Flagging
            # Restore DateTime index for time-based interpolation
            df_station = df_station.set_index("fecha", drop=False)

            for col in cols_continuous:
                if col in df_station.columns:
                    # Create Flag: 1 = Estimated (Originally Missing), 0 = Real
                    df_station[f"{col}_est"] = df_station[col].isna().astype(int)

                    # A. Linear Interpolation (Short gaps)
                    df_station[col] = df_station[col].interpolate(
                        method="linear", limit=7
                    )

                    # B. Climatological Imputation (Long gaps)
                    if df_station[col].isna().any():
                        # Day of Year Mean
                        daily_means = df_station.groupby(df_station.index.dayofyear)[
                            col
                        ].transform("mean")
                        df_station[col] = df_station[col].fillna(daily_means)

                        # Month Mean (Fallback)
                        monthly_means = df_station.groupby(df_station.index.month)[
                            col
                        ].transform("mean")
                        df_station[col] = df_station[col].fillna(monthly_means)

                    # C. Final Safety Net (Defaults)
                    fill_val = 1013.0 if col == "presion" else 0.0
                    df_station[col] = df_station[col].ffill().bfill().fillna(fill_val)

            # Rain & Wind Direction Handling
            df_station["prec_est"] = df_station["prec"].isna().astype(int)
            df_station["prec"] = df_station["prec"].fillna(0.0)

            if "dir" in df_station.columns:
                df_station["dir_est"] = df_station["dir"].isna().astype(int)
                df_station["dir"] = pd.to_numeric(df_station["dir"], errors="coerce")
                df_station["dir"] = df_station["dir"].ffill().bfill().fillna(0)

            df_list.append(df_station.reset_index(drop=True))

        return pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

    def audit_data(self, df: pd.DataFrame):
        """Prints a quality report of the processed dataset."""
        log.info("\n📊 === DATA QUALITY AUDIT ===")

        # Physical Clips
        if "hrMedia" in df.columns:
            df["hrMedia"] = df["hrMedia"].clip(0, 100)
        if "sol" in df.columns:
            df["sol"] = df["sol"].clip(0, 24)
        if "nubes" in df.columns:
            df["nubes"] = df["nubes"].clip(0, 100)

        # Estimation Analysis
        est_cols = [c for c in df.columns if c.endswith("_est")]

        if est_cols:
            log.info("📉 % Estimated Data by Variable (Global Average):")
            for col in est_cols:
                pct = df[col].mean() * 100
                log.info(f"   - {col.replace('_est', '').upper()}: {pct:.2f}%")

            # Worst Stations
            df["_quality_score"] = df[est_cols].mean(axis=1)
            station_quality = df.groupby("nombre")["_quality_score"].mean() * 100
            worst = station_quality.sort_values(ascending=False).head(5)

            log.info("\n🏆 Bottom 5 Stations (Highest Estimation Ratio):")
            for name, score in worst.items():
                log.info(f"   ⚠️ {name}: {score:.2f}% estimated")

            df = df.drop(columns=["_quality_score"])

        n_stations = df["indicativo"].nunique()
        log.info(f"\n✅ Finished. Stations: {n_stations}. Rows: {len(df)}")

    def execute(self):
        """Main execution method."""
        df = self.load_and_validate()
        df = self.filter_bad_stations(df)
        df = self.process_stations_logic(df)
        self.audit_data(df)

        df = df.sort_values(["indicativo", "fecha"]).reset_index(drop=True)

        output_path = self.processed_dir / "weather_dataset_clean.csv"
        df.to_csv(output_path, index=False)
        log.info(f"✨ Final Dataset Saved: {output_path}")
