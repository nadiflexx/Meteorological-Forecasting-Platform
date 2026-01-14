# 🏗️ System Architecture

## Overview

Rainbow AI adopts a **Modular Layered Architecture** that cleanly separates Data Engineering, Machine Learning, and User Interface concerns. This design enables rigorous testing, horizontal scalability, and maintainable code evolution.

---

## 🌳 Complete Directory Structure

```
Meteorological-Prediction-System/
│
├── 📂 pipelines/                    # ORCHESTRATION LAYER
│   │                                # (7 sequential execution pipelines)
│   ├── 01_ingest_data.py            # ETL Stage 1: Download AEMET (2009–2025)
│   ├── 02_process_data.py           # ETL Stage 2: Clean & enrich with Open-Meteo
│   ├── 03_train_model.py            # ML Stage 1: Train 7 models & forecast
│   ├── 04_onestep_forecast.py       # Validation 1: Teacher forcing (maximum accuracy)
│   ├── 05_recursive_forecast.py     # Validation 2: Multi-step (realistic errors)
│   ├── 06_comparative_report.py     # Validation 3: Metrics & plots
│   ├── 07_model_analysis.py         # Validation 4: Feature importance & residuals
│   ├── best_params.py               # Hyperparameter tuning utilities
│   ├── best_threshold.py            # Rain classification threshold optimization
│   └── actions/                     # Supplementary action scripts
│
├── 📂 src/                          # BACKEND CORE
│   │                                # (Domain logic & scientific computation)
│   ├── 📂 config/
│   │   └── settings.py              # Single Source of Truth: Paths, APIs, Models, Features
│   │
│   ├── 📂 etl/                      # EXTRACT-TRANSFORM-LOAD
│   │   ├── 📂 clients/
│   │   │   ├── aemet.py             # AEMET OpenData API (Rate-limit handling)
│   │   │   └── openmeteo.py         # Open-Meteo Archive API (Pressure, clouds)
│   │   ├── ingestion.py             # File I/O & atomic writes
│   │   └── processing.py            # Fusion, validation, cleaning, imputation
│   │
│   ├── 📂 features/                 # FEATURE ENGINEERING
│   │   ├── transformation.py        # Lags, rolling windows, cyclical encoding
│   │   └── physics.py               # Magnus formula, VPD, RH calculations
│   │
│   ├── 📂 modeling/                 # MACHINE LEARNING
│   │   ├── base.py                  # BaseModel: LightGBM wrapper
│   │   │                            # (fit, save, load, predict, explain)
│   │   ├── 📂 trainers/
│   │   │   ├── rain.py              # RainClassifier (Binary: rain/no-rain)
│   │   │   ├── temperature.py       # TemperatureModel (3 regressors)
│   │   │   └── atmosphere.py        # AtmosphereModel (3 regressors)
│   │   ├── rainbow.py               # RainbowCalculator (Heuristic logic)
│   │   └── wind_chill.py            # WindChillCalculator (Apparent temp)
│   │
│   ├── 📂 schemas/                  # DATA VALIDATION
│   │   └── weather.py               # Pydantic models (WeatherRecord, StationMetadata)
│   │
│   └── 📂 utils/                    # SHARED UTILITIES
│       ├── logger.py                # Logging (file + console)
│       ├── constants.py             # Global constants (station IDs, variable names)
│       └── helpers.py               # Generic helper functions
│
├── 📂 app/                          # PRESENTATION LAYER
│   │                                # (Streamlit frontend)
│   ├── main.py                      # App entry point & layout
│   ├── 📂 pages/
│   │   ├── 01_Rainbow_Hunter.py     # Page 1: Rainbow probability detector
│   │   ├── 02_Model_Audit.py        # Page 2: Performance metrics & validation
│   │   ├── 03_Weather_Forecast.py   # Page 3: 21-day forecast maps & charts
│   │   └── 04_Wind_Chill_Notify_Form.py  # Page 4: Apparent temp calculator
│   │
│   ├── 📂 components/
│   │   ├── charts.py                # Plotly charts (scatter, line, box)
│   │   ├── maps.py                  # Folium geospatial maps
│   │   ├── visuals.py               # Custom styling & widgets
│   │   └── loading.py               # Caching & data loaders
│   │
│   └── 📂 assets/
│       └── style.css                # CSS styling
│
├── 📂 data/                         # DATA LAYER
│   ├── 📂 raw/
│   │   ├── Station_Metadata.json    # Station coordinates & metadata
│   │   └── Station_*/               # 21 folders (one per station)
│   │       ├── 2009.json
│   │       ├── 2010.json
│   │       └── ... (one file per year)
│   │
│   ├── 📂 processed/
│   │   └── weather_dataset_clean.csv  # Unified clean training data
│   │
│   └── 📂 predictions/
│       ├── rainbow_forecast_final.csv # Final 21-day forecast output
│       ├── 📂 predictions_comparation/
│       ├── 📂 model_analysis/
│       └── 📂 comparative/
│
├── 📂 models/                       # ML ARTIFACTS
│   ├── lgbm_rain.pkl                # Rain classifier (binary)
│   ├── lgbm_tmed.pkl                # Mean temp regressor
│   ├── lgbm_tmin.pkl                # Min temp regressor
│   ├── lgbm_tmax.pkl                # Max temp regressor
│   ├── lgbm_sol.pkl                 # Solar radiation regressor
│   ├── lgbm_hrMedia.pkl             # Humidity regressor
│   └── lgbm_velmedia.pkl            # Wind speed regressor
│
├── 📂 tests/                        # TEST SUITE
│   ├── __init__.py
│   ├── 📂 config/
│   ├── 📂 etl/
│   ├── 📂 features/
│   ├── 📂 modeling/
│   ├── 📂 schemas/
│   └── 📂 utils/
│
├── 📂 docs/                         # DOCUMENTATION
│   ├── index.md                     # Main overview (this project)
│   ├── architecture.md              # System design (this file)
│   ├── pipelines.md                 # Pipeline descriptions
│   ├── logic.md                     # Feature & model logic
│   ├── app_structure.md             # Frontend pages & components
│   ├── results.md                   # Performance metrics
│   └── CONTRIBUTING.md              # Developer guide
│
├── pyproject.toml                   # Project metadata & dependencies
├── mkdocs.yml                       # Documentation site config
├── LICENSE                          # Usage rights
└── README.md                        # Git repository readme
```

---

## 🔄 Data Flow

### Phase 1: Ingestion (ETL Stage 1)

```
┌─────────────────┐
│  AEMET OpenData │  Raw JSON (2009–2025)
└────────┬────────┘  21 stations × 17 years
         │
         ├→ Rate-limit handler
         ├→ Atomic writes (prevent corrupted files)
         ├→ Metadata enrichment
         │
         ▼
    [data/raw/Station_*/*.json]
```

### Phase 2: Processing (ETL Stage 2)

```
[data/raw/Station_*/*.json]
         │
         ├→ Open-Meteo API (pressure, clouds for 2009–2025)
         ├→ Schema validation (Pydantic)
         ├→ Outlier detection & filtering
         ├→ Missing value imputation (forward-fill, interpolation)
         │
         ▼
    [data/processed/weather_dataset_clean.csv]
```

### Phase 3: Feature Engineering

```
[weather_dataset_clean.csv]
         │
         ├→ Lags: T-1, T-2, T-7 days
         ├→ Rolling: 3-day, 7-day, 14-day windows
         ├→ Cyclical: sin/cos(day-of-year), sin/cos(month)
         ├→ Physics: Magnus formula, VPD, RH from dew point
         │
         ▼
    [featurized_dataset]
```

### Phase 4: Model Training

```
[featurized_dataset]
         │
         ├─→ Train/Val/Test Split (2009–2023 / 2024 / 2025)
         │
         ├─→ 7 LightGBM Models:
         │   ├─ Rain Classifier (Binary)
         │   ├─ Temperature Models (Mean, Min, Max)
         │   └─ Atmosphere Models (Solar, Humidity, Wind)
         │
         ├─→ Cross-validation & hyperparameter tuning
         │
         ▼
    [models/lgbm_*.pkl]
```

### Phase 5: Forecasting

```
[Latest processed data + 7 trained models]
         │
         ├─→ One-Step Forecast (teacher forcing)
         │   └→ Maximum theoretical accuracy
         │
         ├─→ Recursive Forecast (21 days)
         │   └→ Uses predictions as inputs (realistic error)
         │
         ├─→ Rainbow Heuristic: rain_score × sun_score × humidity
         │
         ├─→ Wind Chill: 3 formulas (Standard, Heat Index, Steadman)
         │
         ▼
    [data/predictions/rainbow_forecast_final.csv]
```

### Phase 6: Visualization

```
[rainbow_forecast_final.csv]
         │
         ├→ Streamlit Dashboard
         │  ├─ Page 1: Rainbow probability with SVG viz
         │  ├─ Page 2: Scatter plots (actual vs. predicted)
         │  ├─ Page 3: 21-day forecast with maps
         │  └─ Page 4: Wind chill calculator
         │
         ├→ Plotly charts (interactive)
         ├→ Folium maps (geospatial)
         │
         ▼
    [Web Browser (localhost:8501)]
```

---

## 🤖 The 7 Models

### Overview

| Model       | Type              | Target Variable   | Input Features               | Output      | Train Data |
| ----------- | ----------------- | ----------------- | ---------------------------- | ----------- | ---------- |
| **Model 1** | Binary Classifier | Precipitation     | 21 temporal + 6 weather lags | P(rain)     | 2009–2023  |
| **Model 2** | Regressor         | Mean Temperature  | 21 temporal + 6 weather lags | Tmed (°C)   | 2009–2023  |
| **Model 3** | Regressor         | Min Temperature   | 21 temporal + 6 weather lags | Tmin (°C)   | 2009–2023  |
| **Model 4** | Regressor         | Max Temperature   | 21 temporal + 6 weather lags | Tmax (°C)   | 2009–2023  |
| **Model 5** | Regressor         | Solar Radiation   | 21 temporal + 6 weather lags | Sol (hours) | 2009–2023  |
| **Model 6** | Regressor         | Relative Humidity | 21 temporal + 6 weather lags | HR (%)      | 2009–2023  |
| **Model 7** | Regressor         | Wind Speed        | 21 temporal + 6 weather lags | Vel (m/s)   | 2009–2023  |

### Training Configuration

**All models use:**

- **Algorithm:** LightGBM (gradient boosting)
- **Hyperparameters:** See `src/config/settings.py` → `ModelConfig`
- **Feature Set:** 27 features (21 temporal + 6 weather lags)
- **Validation:** 5-fold cross-validation on training set (2009–2023)
- **Test Set:** 2024–2025 (held out for final evaluation)
- **Scaling:** No scaling required for tree-based models

---

## ⚙️ Configuration & Settings

All configuration is centralized in **src/config/settings.py**:

```python
# Example configuration structure
class ModelConfig:
    RAIN_THRESHOLD = 0.3        # Adjust to tune precision/recall
    FORECAST_DAYS = 21
    LAG_DAYS = [1, 2, 7]
    ROLLING_WINDOWS = [3, 7, 14]

class FeatureConfig:
    CYCLICAL_FEATURES = ['dayofyear', 'month']
    WEATHER_VARIABLES = ['tmed', 'tmin', 'tmax', 'sol', 'hrMedia', 'velmedia']

class PathConfig:
    RAW_DATA = 'data/raw/'
    PROCESSED_DATA = 'data/processed/'
    MODELS = 'models/'
    PREDICTIONS = 'data/predictions/'
```

**Best Practice:** Modify configuration in `settings.py`, not in pipeline scripts. This ensures consistency across the entire system.

---

## 🔌 External APIs

### AEMET OpenData

- **Endpoint:** `https://opendata.aemet.es/`
- **Data:** Temperature, wind, humidity, precipitation, solar radiation
- **Coverage:** 2009–2025 for 21 Catalan stations
- **Rate Limit:** 5 requests/second
- **Documentation:** [AEMET API Docs](https://www.aemet.es/es/datos_abiertos/AEMET_OpenData)

### Open-Meteo Archive

- **Endpoint:** `https://archive-api.open-meteo.com/`
- **Data:** Atmospheric pressure, cloud cover, additional physics
- **Coverage:** Historical (1940–present)
- **Rate Limit:** Generous (no strict limit for non-commercial)
- **Documentation:** [Open-Meteo Archive Docs](https://open-meteo.com/en/docs/historical-weather-api)

---

## 📊 Model Explainability

Each trained model includes:

- **Feature Importance (Gain)** – Which features contribute most to predictions
- **Residual Analysis** – Distribution of prediction errors by season
- **Partial Dependence Plots** – Relationship between input features and output

Generated in **Pipeline 07 (model_analysis.py)** and saved to `data/predictions/model_analysis/`.

---

**Architecture Status:** Production-Ready | **Last Updated:** January 2026
