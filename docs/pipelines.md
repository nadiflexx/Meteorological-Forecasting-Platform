# ⚙️ Execution Pipelines

The system is driven by three sequential execution scripts located in the `pipelines/` directory. This is the backbone of the project's automation.

## 1. Data Ingestion (`01_ingest_data.py`)

**Goal:** Build the raw historical dataset from official sources.

- **Source:** Connects to the **AEMET OpenData API**.
- **Scope:** Downloads daily climatological records for **26 meteorological stations** in the Barcelona province.
- **Timeframe:** From **January 1, 2009** to **December 31, 2025**.
- **Methodology:**
  - Since AEMET has a limit on data requests, the script loops in **6-month chunks**.
  - It implements a **Retry Mechanism** with exponential backoff to handle API timeouts (Error 429).
  - Data is saved incrementally to `data/raw/` to prevent data loss during long downloads.
  - Finally, it consolidates daily JSONs into yearly files (e.g., `data_2024.json`).

## 2. Data Processing (`02_process_data.py`)

**Goal:** Clean, enrich, and unify data into a single Training Dataset.

This is the most critical step for data quality. It performs three main operations:

### A. Quality Filtering

It analyzes the raw data from the 26 stations.

- **Logic:** Any station with less than **85% data coverage** over the 15-year period is discarded as unreliable.
- **Result:** The system keeps the best **21 Stations** for training.

### B. Physical Enrichment (Open-Meteo)

AEMET data often lacks key variables for advanced modeling (like atmospheric pressure).

- **Action:** The script calls the **Open-Meteo Historical Archive API** for each of the 21 valid stations.
- **Data Retrieved:**
  - `pressure_msl_mean` (Essential for rain prediction).
  - `cloud_cover_mean` (Crucial for detecting overcast days).
  - `sunshine_duration` (Validates solar models).
- **Benefit:** This drastically reduces the need to "invent" (interpolate) missing values, replacing them with high-quality reanalysis data.

### C. Imputation & Export

- **Short Gaps:** Uses **Linear Interpolation** (filling gaps of 1-7 days based on the trend).
- **Long Gaps:** Uses **Climatological Means** (e.g., filling a missing day with the average of that specific day over 15 years).
- **Output:** Generates `weather_dataset_clean.csv`, ready for Machine Learning.

## 3. Model Training (`03_train_model.py`)

**Goal:** Train AI models and generate future forecasts.

- **Input:** Reads the clean CSV.
- **Feature Engineering:** Creates Lags (t-1, t-2), Rolling Windows, and Seasonality features.
- **Training:** Trains 7 separate **LightGBM** models (Rain, Temp, Wind, etc.).
- **Forecasting:** Generates predictions for the Test Set (2023-2025).
- **Rainbow Logic:** Applies the heuristic formula to the predictions to calculate the `rainbow_prob`.
- **Output:** Saves the final `rainbow_forecast_final.csv`, which powers the Streamlit Dashboard.
