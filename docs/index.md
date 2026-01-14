# 🌈 Rainbow AI: Meteorological Prediction System

## Overview

**Rainbow AI** is a comprehensive Machine Learning-based meteorological prediction system that forecasts 7 climate variables for 21 stations across Catalonia. The project integrates historical data (2009-2025) from AEMET with atmospheric physics from Open-Meteo to deliver accurate 21-day weather predictions.

### 🎯 Key Features

- **🌈 Rainbow Detection** – Identifies optimal rainbow conditions (rain + sun + humidity)
- **📅 21-Day Forecast** – Temperature, wind, solar radiation, humidity, and precipitation
- **📊 Interactive Dashboard** – Streamlit UI with maps, charts, and real-time updates
- **🤖 7 LightGBM Models** – Scientifically trained and rigorously evaluated
- **❄️ Apparent Temperature** – Wind Chill and Heat Index calculations for perceived temperature

---

## 🚀 Quick Start

### Prerequisites

```bash
# System requirements
- Python 3.10 or higher
- uv (Python package manager)
- AEMET API Key (set in .env as AEMET_API_KEY)
```

### Complete Execution Pipeline

#### Step 1: Download Historical Data

```bash
uv run pipelines/01_ingest_data.py
```

Downloads AEMET data for 2009–2025 across 21 stations. **Duration: 4–6 hours**

#### Step 2: Process & Enrich Data

```bash
uv run pipelines/02_process_data.py
```

Cleans, validates, enriches with Open-Meteo physics, and imputes missing values. **Duration: ~30 minutes**

#### Step 3: Train Models & Generate Forecast

```bash
uv run pipelines/03_train_model.py
```

Trains 7 LightGBM models and generates the 21-day forecast. **Duration: ~10 minutes**

#### Step 4: Launch Interactive Dashboard

```bash
uv run streamlit run app/main.py
```

Opens the web interface for interactive exploration and visualization.

**Total Duration: 5–7 hours** (mainly from AEMET download)

---

## 🔍 Optional Validation Steps

After the main pipeline, run additional analyses:

```bash
# One-step forecast (maximum theoretical accuracy with teacher forcing)
uv run pipelines/04_onestep_forecast.py

# Recursive forecast (realistic error accumulation across 21 days)
uv run pipelines/05_recursive_forecast.py

# Comparative analysis report
uv run pipelines/06_comparative_report.py

# Model explainability and feature importance
uv run pipelines/07_model_analysis.py
```

---

## 📈 Expected Results

### Model Performance Metrics

| Variable              | Metric  | Value    | Quality       |
| --------------------- | ------- | -------- | ------------- |
| **Precipitation**     | ROC-AUC | 0.72     | ✅ Good       |
| **Mean Temperature**  | MAE     | 1.19°C   | 🚀 Excellent  |
| **Min Temperature**   | MAE     | 1.28°C   | ✅ Very Good  |
| **Max Temperature**   | MAE     | 1.65°C   | ✅ Good       |
| **Wind Speed**        | MAE     | 0.52 m/s | 🚀 Excellent  |
| **Solar Radiation**   | MAE     | 1.53 h   | ⚠️ Acceptable |
| **Relative Humidity** | MAE     | ~7.7%    | ⚠️ Acceptable |

**Details:** See [Results](results.md) for interpretation and one-step vs. recursive degradation.

---

## 📁 Project Structure

```
Meteorological-Prediction-System/
│
├── pipelines/                  # 7 orchestration scripts (ETL → ML → Validation)
│   ├── 01_ingest_data.py
│   ├── 02_process_data.py
│   ├── 03_train_model.py
│   ├── 04_onestep_forecast.py
│   ├── 05_recursive_forecast.py
│   ├── 06_comparative_report.py
│   └── 07_model_analysis.py
│
├── src/                        # Backend core
│   ├── config/                 # Centralized configuration
│   ├── etl/                    # Data ingestion & processing
│   ├── features/               # Feature engineering
│   ├── modeling/               # ML models & heuristics
│   ├── schemas/                # Data validation
│   └── utils/                  # Shared utilities
│
├── app/                        # Frontend (Streamlit)
│   ├── main.py
│   ├── pages/                  # 4 interactive pages
│   ├── components/             # Reusable UI widgets
│   └── assets/                 # CSS styles
│
├── data/                       # Data storage
│   ├── raw/                    # AEMET JSON files
│   ├── processed/              # Clean training dataset
│   └── predictions/            # Forecast outputs
│
├── models/                     # Trained LightGBM artifacts
│
├── tests/                      # Unit & integration tests
│
└── docs/                       # Documentation (this folder)
```

---

## 📚 Documentation Index

| Document                             | Purpose                                                              |
| ------------------------------------ | -------------------------------------------------------------------- |
| [Architecture.md](architecture.md)   | System design, folder structure, data flows, 7 models                |
| [Pipelines.md](pipelines.md)         | Detailed description of each execution pipeline (01–07)              |
| [Logic.md](logic.md)                 | Feature engineering, ML models, rainbow & wind chill heuristics      |
| [App Structure.md](app_structure.md) | Streamlit dashboard pages, components, user personas                 |
| [Results.md](results.md)             | Performance metrics, interpretation, one-step vs. recursive analysis |
| [Contributing.md](CONTRIBUTING.md)   | Developer setup, code style, testing guidelines                      |

---

## 💡 Getting Help

- Check [Results.md](results.md) for metric interpretation
- See [Pipelines.md](pipelines.md) for execution details
- Review [Contributing.md](CONTRIBUTING.md) for development setup
- View LICENSE in project root for usage rights

---

## 🎨 Visualization Examples

All interactive visualizations are powered by:

- **Plotly** for dynamic charts (scatter, line, box plots)
- **Folium** for geospatial maps with station markers
- **Streamlit** for reactive UI and caching

Outputs are saved to `data/predictions/` for further analysis.

---

**Status:** Production-Ready | **Last Updated:** January 2026 | **Python:** 3.10+ | **License:** MIT
