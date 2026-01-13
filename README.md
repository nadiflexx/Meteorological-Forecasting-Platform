# 🌈 Rainbow AI: Meteorological Prediction System

![Python](https://img.shields.io/badge/Python-3.13%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red)
![ML](https://img.shields.io/badge/ML-LightGBM-green)
![Status](https://img.shields.io/badge/Status-Validation_Complete-success)
![Coverage](https://img.shields.io/badge/Coverage-80%25-brightgreen?style=for-the-badge)

**Rainbow AI** is an End-to-End Machine Learning system designed to forecast complex meteorological conditions in Catalonia.

Beyond standard weather metrics, it features specialized heuristics to predict **Optical Phenomena (Rainbows)** and human-centric metrics like **Wind Chill** ("Feels Like" temperature). It relies on a robust architecture fed by **AEMET** and **Open-Meteo** historical data.

---

## 📚 Full Documentation

For a deep dive into the architecture, physics, and validation reports:

👉 **[Read the Full Documentation](docs/index.md)**  
_(Run `uv run mkdocs serve` to view locally)_

---

## 🏗️ Architecture Overview

The project follows a **Modular Layered Architecture**, managed by a **Single Source of Truth (SSOT)** configuration.

### 📁 Project Structure

    METEOROLOGICAL-PREDICTION-SYSTEM/
    ├── 📂 app/               # Presentation Layer (Streamlit Dashboard)
    ├── 📂 pipelines/         # Execution Orchestrators
    │   ├── 01_ingest_data.py       # ETL: Download AEMET data
    │   ├── 02_process_data.py      # ETL: Clean & Enrich (Open-Meteo)
    │   ├── 03_train_model.py       # ML: Train Models & Export App Data
    │   ├── 04_onestep_forecast.py  # Test: Validation (Short-term accuracy)
    │   ├── 05_recursive_forecast.py# Test: Simulation (Long-term stability)
    │   ├── 06_comparative_report.py# Test: Audit & Plotting
    ├   └── 07_model_analysis.py    # Test: Visualization
    ├── 📂 src/               # Backend Core Logic
    │   ├── 📂 config/        # SSOT (Settings, feature configs, file names)
    │   ├── 📂 features/      # Feature Engineering (Lags, Rolling, Physics)
    │   └── 📂 modeling/      # LightGBM Trainers & Heuristics (Rainbow/WindChill)
    └── 📂 docs/              # Technical Documentation

---

## 🚀 Key Features

- **🌈 Rainbow Heuristic:** Probabilistic score derived from rain, sunshine duration, and humidity.
- **❄️ Wind Chill Engine:** Calculates "Apparent Temperature" using Steadman and Heat Index formulas based on ML predictions.
- **🌧️ Rain Classifier:** Robust LightGBM model using pressure trends to detect incoming precipitation.
- **🧪 rigorous Validation:** Includes pipelines for One-Step Ahead forecasting and Recursive Simulation to audit model degradation.

---

## 🛠️ Quick Start

### 1️⃣ Installation

    git clone https://github.com/nadiflexx/Meteorological-Forecasting-Platform.git
    uv sync

### 2️⃣ Configuration

Create a `.env` file:

AEMET_API_KEY="your_key_here"
TELEGRAM_BOT_TOKEN="your_telegram_token_here"

---

### 3️⃣ Execution Flow (Pipelines)

Run the pipelines in order:

# 1. ETL: Ingest & Process (2009-2025)

uv run pipelines/01_ingest_data.py
uv run pipelines/02_process_data.py

# 2. ML: Train Models & Generate App Data

uv run pipelines/03_train_model.py

# 3. (Optional) Audit: Validate Model Performance

uv run pipelines/04_onestep_forecast.py
uv run pipelines/05_recursive_forecast.py
uv run pipelines/06_comparative_report.py
uv run pipelines/07_model_analysis.py

---

### 4️⃣ Launch Application

    uv run streamlit run app/main.py

---

## 📊 Performance & Results

Metrics obtained from the test set:

| Target        | Model Type | Metric  | Performance          |
| ------------- | ---------- | ------- | -------------------- |
| Precipitation | Classifier | ROC-AUC | 0.71 (Robust)        |
| Temperature   | Regressor  | MAE     | 1.09 °C (Excellent)  |
| Wind Speed    | Regressor  | MAE     | 0.51 m/s (Excellent) |
| Humidity      | Regressor  | MAE     | ~7.2 % (Acceptable)  |

## 👥 Authors

- Nadeem Rashid
- Albert Grau
- Joan Albert Chias

---

## 📄 License

This project is licensed under the MIT License.
See the `LICENSE` file for details.

---
