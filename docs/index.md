# 🌈 Rainbow AI: Meteorological Prediction System

**Rainbow AI** is a comprehensive Machine Learning solution designed to forecast complex meteorological conditions in Catalonia.

While its flagship feature is the prediction of **Optical Phenomena (Rainbows)**, the system functions as a full-scale **Weather Simulator**, predicting 7 distinct variables for 21 meteorological stations using historical data from AEMET and Open-Meteo.

## 🎯 Project Goals

1.  **Rainbow Prediction:** Detect the "Goldilocks Zone" where rain, sun, and humidity align to form rainbows.
2.  **General Weather Forecasting:** Generate 24h forecasts for Temperature (Min/Max/Avg), Wind, and Precipitation.
3.  **Technical Audit:** Provide a transparent layer to evaluate the AI's performance against real historical data.

## 🚀 Quick Start

To generate predictions from scratch, you must run the pipelines in sequential order:

### 1. Ingest Data (ETL)

Downloads raw daily records (2009-2025) from the **AEMET API**.

```bash
uv run pipelines/01_ingest_data.py
```

### 2. Process & Enrich

Cleans the data, merges it with Open-Meteo physics (Pressure, Clouds), and performs imputation.

```bash
uv run pipelines/02_process_data.py
```

### 3. Train Models

Trains the LightGBM engines and generates the final forecast CSV.

```bash
uv run pipelines/03_train_model.py
```

### 4. Launch Dashboard

Start the interactive Streamlit interface.

```bash
uv run streamlit run app/main.py
```
