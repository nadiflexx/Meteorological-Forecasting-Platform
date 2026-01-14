# 📦 Pipelines: Execution Workflow

## Overview

The system orchestrates data processing and model training through **7 sequential pipelines**, each handling a specific stage of the ETL-ML-Validation workflow.

---

## 🚀 Pipeline Execution Order

```
Stage 1: INGESTION      Stage 2: PROCESSING     Stage 3: ML            Stage 4: VALIDATION
┌──────────────────┐    ┌──────────────────┐    ┌───────────────────┐  ┌──────────────────────┐
│ 01_ingest_data   │ → │ 02_process_data  │ → │ 03_train_model   │ → │ 04_onestep_forecast  │
└──────────────────┘    └──────────────────┘    └───────────────────┘  └──────────────────────┘
  (4–6 hours)            (~30 minutes)           (~10 minutes)          (Optional: ~5 minutes)

                                                                        ┌──────────────────────┐
                                                                        │ 05_recursive_forecast│
                                                                        └──────────────────────┘
                                                                        (Optional: ~10 minutes)

                                                                        ┌──────────────────────┐
                                                                        │ 06_comparative_report│
                                                                        └──────────────────────┘
                                                                        (Optional: ~15 minutes)

                                                                        ┌──────────────────────┐
                                                                        │ 07_model_analysis    │
                                                                        └──────────────────────┘
                                                                        (Optional: ~10 minutes)
```

---

## 📥 Pipeline 01: Ingest Data

**Purpose:** Download raw meteorological data from AEMET for historical years (2009–2025).

### Execution

```bash
uv run pipelines/01_ingest_data.py
```

### What It Does

- Calls AEMET OpenData API for 21 Catalan stations
- Downloads all available years (2009–2025) in JSON format
- Implements rate-limit handling (5 req/sec max)
- Writes atomically (prevents corrupt files on interruption)
- Stores in `data/raw/Station_*/*.json`

### Input

- **.env** (AEMET_API_KEY)
- Station list from `src/config/settings.py`

### Output

- `data/raw/Station_0061X_Pontons/2009.json`
- `data/raw/Station_0061X_Pontons/2010.json`
- ... (and 20 more stations, 17 years each)

### Duration

**4–6 hours** (depends on API rate-limiting and network latency)

### Success Indicators

- No ERROR messages in console
- All JSON files present in `data/raw/`
- File sizes > 10 KB (not empty)

---

## 🔧 Pipeline 02: Process Data

**Purpose:** Clean, validate, enrich, and prepare data for ML training.

### Execution

```bash
uv run pipelines/02_process_data.py
```

### What It Does

1. **Load & Merge** – Reads all raw JSON files into a single DataFrame
2. **Enrich** – Calls Open-Meteo API for pressure & cloud cover data
3. **Validate** – Checks for data type, range, and schema errors (Pydantic)
4. **Filter** – Removes outliers (e.g., temperature > 50°C)
5. **Impute** – Fills missing values using forward-fill and interpolation
6. **Standardize** – Ensures consistent column names and units

### Input

- `data/raw/Station_*/*.json`
- Open-Meteo API (enrichment)

### Output

- `data/processed/weather_dataset_clean.csv`

**CSV Structure:**
| Station | Date | Tmed | Tmin | Tmax | Sol | HRMedia | VelMedia | Prec | Pressure | CloudCover |
|---------|------|------|------|------|-----|---------|----------|------|----------|------------|
| 0061X | 2009-01-01 | 8.5 | 3.2 | 14.1 | 2.3 | 65 | 2.1 | 0.0 | 1013 | 45 |

### Duration

**~30 minutes** (API enrichment takes longest)

### Success Indicators

- `weather_dataset_clean.csv` created (100+ MB)
- No NaN values (all imputed)
- 21 stations × 17 years × 365 days ≈ 130K rows

---

## 🤖 Pipeline 03: Train Model & Forecast

**Purpose:** Feature engineering, model training, and 21-day forecast generation.

### Execution

```bash
uv run pipelines/03_train_model.py
```

### What It Does

1. **Feature Engineering**

   - Lags: T-1, T-2, T-7 days
   - Rolling: 3-day, 7-day, 14-day windows
   - Cyclical: sin/cos(day-of-year), sin/cos(month)
   - Physics: Magnus formula, VPD, relative humidity

2. **Train/Val/Test Split**

   - Train: 2009–2023
   - Validation: 2024 (internal evaluation)
   - Test: 2025 (held-out for final assessment)

3. **Train 7 LightGBM Models**

   ```
   ├─ Rain Classifier (binary: rain/no-rain)
   ├─ Temperature Models (mean, min, max)
   └─ Atmosphere Models (solar, humidity, wind)
   ```

4. **Generate Forecast**

   - Applies all 7 models to latest data
   - Recursive prediction for 21 days ahead

5. **Apply Heuristics**
   - Rainbow probability = rain_score × sun_score × humidity_factor
   - Wind chill = 3 formulas (Standard WC, Heat Index, Steadman)

### Input

- `data/processed/weather_dataset_clean.csv`

### Output

- `models/lgbm_rain.pkl` ... `models/lgbm_velmedia.pkl` (7 models)
- `data/predictions/rainbow_forecast_final.csv`

### Duration

**~10 minutes**

### Success Indicators

- 7 .pkl files in `models/` folder
- `rainbow_forecast_final.csv` has 21 rows (days ahead) × 7 columns (variables)
- No NaN values in forecast

---

## ✅ Pipeline 04: One-Step Forecast

**Purpose:** Validate model accuracy using "teacher forcing" (providing real previous day values).

### Execution

```bash
uv run pipelines/04_onestep_forecast.py
```

### What It Does

- For each day in test set (2025), predicts using **actual previous day values**
- Generates error metrics (MAE, RMSE, R²)
- Produces scatter plots (predicted vs. actual)

### Input

- Trained models from Pipeline 03
- `data/processed/weather_dataset_clean.csv` (2025 subset)

### Output

- `data/predictions/predictions_comparation/onestep_*.csv`
- `data/predictions/model_analysis/onestep_scatter_*.png`

### Duration

**~5 minutes**

### Notes

- **Maximum theoretical accuracy** (assumes perfect prior forecasts)
- Error metrics are lower than recursive approach
- Use as baseline for model performance

---

## 🔄 Pipeline 05: Recursive Forecast

**Purpose:** Realistic multi-step forecasting using predicted values as inputs.

### Execution

```bash
uv run pipelines/05_recursive_forecast.py
```

### What It Does

- Day 1: Predicts using actual prior values
- Day 2: Predicts using predicted Day 1 values
- Day 3–21: Predicts using predicted prior values
- Error accumulates over time (realistic scenario)

### Input

- Trained models from Pipeline 03
- Starting data (latest available)

### Output

- `data/predictions/predictions_comparation/recursive_21day.csv`
- `data/predictions/model_analysis/recursive_degradation_*.png`

### Duration

**~10 minutes**

### Notes

- **Realistic error accumulation** over 21 days
- Expected degradation: ~30–50% by day 21
- Use for understanding forecast reliability

---

## 📊 Pipeline 06: Comparative Report

**Purpose:** Generate comprehensive performance metrics and visualization report.

### Execution

```bash
uv run pipelines/06_comparative_report.py
```

### What It Does

- Compares one-step vs. recursive forecasts
- Computes MAE, RMSE, R², ROC-AUC by variable
- Creates comparison plots (error degradation by day)
- Generates seasonal breakdown (summer vs. winter performance)

### Input

- Output from Pipelines 04 & 05
- Test set data (2025)

### Output

- `data/predictions/comparative/metrics_summary.csv`
- `data/predictions/comparative/comparison_plots/*.png`
- Console: Summary statistics printed

### Duration

**~15 minutes**

### Success Indicators

- All PNG plots generated
- `metrics_summary.csv` contains 7 variables × 4 metrics

---

## 🔬 Pipeline 07: Model Analysis & Explainability

**Purpose:** Analyze feature importance and model behavior for interpretability.

### Execution

```bash
uv run pipelines/07_model_analysis.py
```

### What It Does

1. **Feature Importance (Gain)**

   - Identifies which features most influence each model
   - Ranks features by contribution

2. **Residual Analysis**

   - Distribution of prediction errors
   - Error patterns by season/station

3. **Partial Dependence Plots**
   - How output changes with each input feature
   - Non-linear relationships visualization

### Input

- Trained 7 models
- Test set data (2025)

### Output

- `data/predictions/model_analysis/feature_importance_*.png`
- `data/predictions/model_analysis/residuals_*.png`
- `data/predictions/model_analysis/partial_dependence_*.png`

### Duration

**~10 minutes**

### Success Indicators

- 3 × 7 = 21 PNG plots generated
- Console output showing top 10 features per model

---

## 🎯 Production Execution Flow

### Recommended Sequence

```bash
# 1. One-time setup (only on first run)
uv run pipelines/01_ingest_data.py      # 4–6 hours
uv run pipelines/02_process_data.py     # ~30 minutes

# 2. Regular training & prediction
uv run pipelines/03_train_model.py      # ~10 minutes
# ... forecast is now ready in data/predictions/

# 3. Optional: validation & analysis
uv run pipelines/04_onestep_forecast.py
uv run pipelines/05_recursive_forecast.py
uv run pipelines/06_comparative_report.py
uv run pipelines/07_model_analysis.py
```

### Quick Setup (Development)

```bash
# Skip ingestion if you have recent data
uv run pipelines/02_process_data.py     # Reprocess existing raw data
uv run pipelines/03_train_model.py      # Retrain & generate forecast
uv run streamlit run app/main.py        # Launch dashboard
```

---

## ⚠️ Operational Notes

### Handling Interruptions

- **Pipeline 01:** Restarts from last year (implements resume logic)
- **Pipelines 02–07:** No resume; restart from beginning

### Data Backup

- Before running Pipeline 01, backup `data/raw/` (optional but recommended)
- `data/processed/` and `data/predictions/` are regenerated by pipelines

### Troubleshooting

| Issue                           | Solution                                              |
| ------------------------------- | ----------------------------------------------------- |
| **Pipeline 01 times out**       | Check AEMET API status; retry with reduced year range |
| **Pipeline 02 missing columns** | Ensure AEMET API response format hasn't changed       |
| **Pipeline 03 model not found** | Confirm Pipeline 03 completed successfully            |
| **Predictions have NaN**        | Check for missing data in 2025 (may need imputation)  |

---

**Pipeline Status:** Production-Ready | **Last Updated:** January 2026
