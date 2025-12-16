# 🌈 Rainbow AI: Meteorological Prediction System

![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![ML](https://img.shields.io/badge/ML-LightGBM-green)
![Status](https://img.shields.io/badge/Status-Production-success)

**Rainbow AI** is an End-to-End Machine Learning system designed to forecast complex meteorological conditions in Catalonia.

While its flagship feature is the prediction of **Optical Phenomena (Rainbows)**, the system functions as a full-scale **Weather Simulator**, predicting Temperature, Wind, Rain, and Humidity for 21 municipalities using 15 years of historical data.

---

## 📚 Full Documentation

This README provides a quick overview. For a deep dive into the architecture, physics, and code:

👉 **[Read the Full Documentation](docs/index.md)** (or run `uv run mkdocs serve` locally).

---

## 🏗️ Architecture Overview

The project follows a **Modular Layered Architecture**, separating logic (`src`) from execution (`pipelines`) and presentation (`app`).

```text
METEOROLOGICAL-PREDICTION-SYSTEM/
├── 📂 app/               # Presentation Layer (Streamlit Dashboard)
├── 📂 pipelines/         # Execution Orchestrators (Ingest -> Process -> Train)
├── 📂 src/               # Backend Core Logic
│   ├── config/           # Single Source of Truth (Settings)
│   ├── etl/              # Data Engineering (AEMET + Open-Meteo)
│   ├── features/         # Feature Engineering (Lags, Rolling, Cyclical)
│   └── modeling/         # Machine Learning Trainers (LightGBM)
└── 📂 docs/              # Technical Documentation
🚀 Key Features
🌈 Rainbow Heuristic: A probabilistic score derived from Rain, Sunshine, and Humidity predictions.
🌧️ Rain Classifier: A robust LightGBM model that uses Pressure Trends to detect incoming storms (AUC 0.73).
🔌 Resilient ETL: Handles API rate limits (429), connection pooling, and atomic file writing.
📊 Interactive Dashboard: A professional UI to visualize forecasts and audit model performance.
🛠️ Quick Start
1. Installation
Clone the repo and install dependencies:

Bash

git clone https://github.com/your-username/rainbow-ai.git
cd rainbow-ai
uv sync
2. Configuration
Create a .env file in the root directory:

env

AEMET_API_KEY="your_api_key_here"
3. Execution Flow (The Pipelines)
You must run these in order to build the dataset:

Bash

# 1. Download raw data (AEMET 2009-2025)
uv run pipelines/01_ingest_data.py

# 2. Clean, merge Open-Meteo physics & impute gaps
uv run pipelines/02_process_data.py

# 3. Train ML models & generate Forecasts
uv run pipelines/03_train_model.py
4. Launch App
Bash

uv run streamlit run app/main.py
📊 Performance & Results
Metrics obtained from the Test Set (2023-2025):

Target	Model Type	Metric	Performance
Precipitation	Classifier	ROC-AUC	0.73 (Robust)
Temperature	Regressor	MAE	1.18 °C (Excellent)
Wind Speed	Regressor	MAE	0.52 m/s (Excellent)
Humidity	Regressor	MAE	~7.6 % (Acceptable)
🌈 Prediction Example
Date: 2025-03-08
Station: Fogars de Montclús
Probability: 81.3%
Scenario: High Rain probability (70%) combined with sun breaks (6.4h) and high humidity.
Author: Nadeem | License: MIT
```
