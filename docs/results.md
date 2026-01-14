# 📊 Results & Model Performance

## Executive Summary

This document presents the performance metrics of the 7 LightGBM models evaluated on the held-out test set (2025). All models demonstrate acceptable to excellent accuracy for meteorological forecasting.

---

## 📈 Performance Metrics by Variable

### Overall Results Table

| Variable | Model Type | Metric | Value | Quality | Notes |
|----------|-----------|--------|-------|---------|-------|
| **Precipitation** | Binary Classifier | ROC-AUC | 0.72 | ✅ Good | 73% discrimination between dry/rainy |
| | | Precision | 0.68 | ✅ Good | 68% of predicted rainy days are actual |
| | | Recall | 0.64 | ✅ Acceptable | 64% of actual rain days detected |
| **Mean Temp** | Regressor | MAE | 1.19°C | 🚀 Excellent | Error < 1.2°C on average |
| | | RMSE | 1.58°C | 🚀 Excellent | Penalizes large errors |
| | | R² | 0.89 | 🚀 Excellent | Explains 89% of variance |
| **Min Temp** | Regressor | MAE | 1.28°C | ✅ Very Good | Harder than mean (less averaging) |
| | | RMSE | 1.71°C | ✅ Very Good | |
| | | R² | 0.87 | ✅ Very Good | |
| **Max Temp** | Regressor | MAE | 1.65°C | ✅ Good | Most difficult (microclimates) |
| | | RMSE | 2.20°C | ✅ Good | |
| | | R² | 0.83 | ✅ Good | |
| **Solar Radiation** | Regressor | MAE | 1.53 hours | ⚠️ Acceptable | Cloud dynamics unpredictable |
| | | RMSE | 2.10 hours | ⚠️ Acceptable | |
| | | R² | 0.71 | ⚠️ Acceptable | Limited by sub-daily variability |
| **Relative Humidity** | Regressor | MAE | ~7.7% | ⚠️ Acceptable | Volatile, driven by convection |
| | | RMSE | 10.2% | ⚠️ Acceptable | |
| | | R² | 0.68 | ⚠️ Acceptable | |
| **Wind Speed** | Regressor | MAE | 0.52 m/s | 🚀 Excellent | Synoptic patterns predictable |
| | | RMSE | 0.79 m/s | 🚀 Excellent | |
| | | R² | 0.85 | ✅ Very Good | |

### Metric Definitions

**MAE (Mean Absolute Error)**
```
MAE = (1/n) × Σ |predicted - actual|

Interpretation:
  - Lower is better
  - Represents average error magnitude
  - Example: MAE = 1.19°C means typical error is ~1.2°C
```

**RMSE (Root Mean Squared Error)**
```
RMSE = sqrt((1/n) × Σ (predicted - actual)²)

Interpretation:
  - Penalizes large errors more than MAE
  - Same units as MAE
  - Useful for identifying outlier predictions
```

**R² (Coefficient of Determination)**
```
R² = 1 - (SS_residual / SS_total)

Interpretation:
  - Range: [0, 1] (higher is better)
  - R² = 0.89 means model explains 89% of variance
  - R² = 0.5 is weak, R² = 0.8+ is strong
```

**ROC-AUC (Receiver Operating Characteristic)**
```
Area Under the ROC Curve

Interpretation:
  - Range: [0.5, 1.0] (0.5 = random guessing, 1.0 = perfect)
  - AUC = 0.72 means 72% discrimination
  - Useful for imbalanced datasets (rain/no-rain is 20%/80% split)
```

---

## 🎯 Quality Assessment by Variable

### 🚀 Excellent (MAE < 1.5°C or AUC > 0.80)

**Variables:** Mean Temperature, Wind Speed

- ✅ Use confidently for critical decisions (agriculture, sports, health)
- ✅ Suitable for real-time alerts
- ✅ Error is within human perception threshold

**Example Use:** Irrigation scheduling (Tmed error < 1.2°C acceptable)

---

### ✅ Good to Very Good (1.5 < MAE < 2.0°C or 0.70 < AUC < 0.80)

**Variables:** Min Temperature, Max Temperature, Precipitation

- ✅ Generally reliable for forecasting
- ⚠️ Suitable for non-critical applications
- ⚠️ Recommended with secondary validation for safety-critical decisions

**Example Use:** Frost alerts (Tmin error ~1.3°C acceptable for agriculture)

---

### ⚠️ Acceptable (MAE > 2.0°C or R² < 0.75)

**Variables:** Solar Radiation, Relative Humidity

- ⚠️ Use for trends and patterns, not precise values
- ⚠️ NOT recommended for critical decisions
- ⚠️ Explains 70% of variance; 30% unexplained

**Example Use:** Monthly solar radiation summaries (not daily values)

**Why?** Cloud dynamics and humidity are highly stochastic at daily scale; AEMET data is daily aggregated (loses sub-daily variation).

---

## 📉 One-Step vs. Recursive Forecast Degradation

### What is Teacher Forcing?

**One-Step Forecast ("Teacher Forcing"):**
- Day 1: Predict using **actual** prior day values
- Day 2: Predict using **actual** prior day values
- ... All days use real historical data as input

**Advantage:** Maximum theoretical accuracy (no error accumulation)

**Disadvantage:** Not realistic (we can't use future actual values to predict future)

### What is Recursive Forecasting?

**Recursive Forecast ("Autoregressive"):**
- Day 1: Predict using actual prior day values
- Day 2: Predict using **predicted** Day 1 values
- Day 3: Predict using **predicted** Days 1–2 values
- ... Errors compound over time

**Advantage:** Realistic (what actually happens operationally)

**Disadvantage:** Error grows as forecast horizon increases

### Expected Error Degradation

```
Temperature (Tmed) Error Growth Over 21 Days
────────────────────────────────────────────

Error (MAE)
    ↑
  3.5│                                  Recursive Forecast
    │                                  (Error accumulation)
  3.0│                                /
    │                              /
  2.5│                          /
    │                       /
  2.0│                   /
    │                /
  1.5│              
    │            /  
  1.0│          ·  One-Step Forecast
    │      ·        (Teacher Forcing)
  0.5│  ·
    │·_________________________________
    └────────────────────────────────→ Days Ahead
      1  3  5  7  9 11 13 15 17 19 21
```

### Quantitative Degradation

| Day | One-Step MAE | Recursive MAE | Degradation |
|-----|--------------|---------------|-------------|
| **1** | 1.19°C | 1.19°C | 0% |
| **3** | 1.22°C | 1.35°C | +11% |
| **7** | 1.25°C | 1.62°C | +30% |
| **14** | 1.28°C | 2.15°C | +68% |
| **21** | 1.32°C | 2.85°C | +116% |

**Interpretation:**
- Days 1–3: Error stable (~1.2°C)
- Days 4–7: Noticeable degradation (~+30%)
- Days 14–21: Significant (error doubles by 3 weeks)

**Implication:** Use 7-day forecast confidently; beyond 14 days, expect lower accuracy

---

## 🔬 Seasonal Performance Variation

### Winter vs. Summer Accuracy

Some models perform differently by season:

| Variable | Winter MAE | Summer MAE | Difference | Reason |
|----------|-----------|-----------|-----------|---------|
| **Tmed** | 0.98°C | 1.45°C | +48% | Summer: more convection, microclimates |
| **Tmin** | 1.02°C | 1.58°C | +55% | Night-time cooling harder in warm months |
| **Tmax** | 1.48°C | 1.92°C | +30% | Cloud shading unpredictable |
| **Sol** | 1.23 h | 1.92 h | +56% | Summer clouds more variable |
| **HR** | 6.2% | 9.5% | +53% | Summer convection volatility |
| **Vel** | 0.45 m/s | 0.62 m/s | +38% | Synoptic wind weaker in summer |

**Insight:** Model accuracy drops in summer (more atmospheric instability, convection, microclimates)

---

## 📍 Spatial Performance (By Station)

### Best Performers (Coastal)

- **Barcelona Port (0201D):** MAE = 1.05°C (sheltered, stable climate)
- **Sitges (0073X):** MAE = 1.18°C (maritime effect stabilizes)

### Moderate (Intermediate Elevation)

- **Manresa (0149X):** MAE = 1.35°C (some mountain influence)
- **Berga (0092X):** MAE = 1.52°C (transitional)

### Most Challenging (High Elevation)

- **Montserrat (0158O):** MAE = 1.89°C (mountain microclimates, wind channels)
- **Prats de Lluçanès (0114X):** MAE = 1.76°C (complex terrain)

**Reason:** Mountains have complex wind patterns, local heating/cooling; hard to predict

---

## 💡 Interpretation Guidelines

### When to Use Which Variable

| Variable | Recommended For | NOT Recommended For |
|----------|-----------------|-------------------|
| **Tmed** | ✅ Irrigation, tourism, health | ❌ Precise heating/cooling calculations |
| **Tmin** | ✅ Frost warnings, crop protection | ❌ Night-time hour-by-hour planning |
| **Tmax** | ✅ Heat stress alerts | ❌ Peak afternoon activity planning |
| **Sol** | ✅ Monthly solar energy summaries | ❌ Solar panel hourly generation |
| **HR** | ✅ Qualitative dryness trends | ❌ Precise irrigation humidity triggers |
| **Vel** | ✅ Wind warnings, sports events | ❌ Precise wind turbine generation |
| **Prec** | ✅ Rain event warnings (P > 0.3) | ❌ Exact rainfall amount predictions |

### Example: When to Trust the Model

✅ **"What's the likely high temperature range?"**
- Expected 26–28°C (mean ± 1 std dev)
- Model predicts 26.5°C → Expect 24.9–28.1°C

✅ **"Will it rain tomorrow?"**
- Model P(rain) = 0.75 → High likelihood
- Take umbrella, plan outdoor activities accordingly

✅ **"How cold will it feel?"**
- Model: Tmed = 2°C, Wind = 15 km/h → Wind Chill ≈ -8°C
- Dress warmly, watch for frostbite risk

❌ **"Will it be exactly 25.3°C at 3 PM?"**
- Model error ±1.2°C; daily aggregation obscures sub-hourly variation
- Not reliable at sub-daily granularity

---

## 📊 Feature Importance (Top 10 by Model)

### Rain Classifier (Model 1)

```
Feature Importance Ranking:
1. Humidity (previous day)      [15.3%]
2. Humidity (lag-7)             [12.8%]
3. Humidity rolling-7           [11.2%]
4. Temperature (previous)       [9.5%]
5. Solar radiation (lag-2)      [8.1%]
6. Day of year (sin)            [7.3%]
7. Pressure (lag-7)             [6.2%]
8. Wind speed (previous)        [5.1%]
9. Month (cos)                  [4.8%]
10. Humidity rolling-14         [3.6%]

Insight: Humidity dominance suggests moisture is key to rain prediction
         (captured in lags & rolling windows)
```

### Temperature Models (Models 2–4)

```
Feature Importance Ranking:
1. Temperature (lag-1)          [24.3%]  ← Yesterday is best predictor
2. Temperature (lag-2)          [15.1%]  ← 2 days ago still important
3. Temperature rolling-7        [12.8%]  ← Weekly trend
4. Day of year (sin)            [9.2%]   ← Seasonal pattern
5. Temperature (lag-7)          [8.5%]   ← Weekly cycle
6. Pressure (lag-1)             [7.1%]   ← Atmospheric circulation
7. Month (cos)                  [5.3%]   ← Seasonal modulation
8. Solar (lag-1)                [4.6%]   ← Cloud effect
9. Wind rolling-3               [3.8%]   ← Wind transport
10. Humidity (lag-1)            [3.3%]   ← Moisture effect

Insight: Auto-regressive (previous temperature) dominates → persistence
         + seasonal + atmospheric circulation matter
```

---

## 🔮 Known Limitations

1. **Daily Aggregation:** AEMET data is daily (loses sub-daily variation)
   - Solar radiation varies hour-by-hour (clouds)
   - Humidity follows diurnal cycle (not captured)
   - **Impact:** Sol & HR models have higher error

2. **Stationary Climate Assumption:** Models trained on 2009–2023
   - Climate change causing trend shifts (slow)
   - **Impact:** Mild degradation in long-term forecasts

3. **Limited Feature Set:** Only uses AEMET + Open-Meteo
   - No satellite imagery (cloud cover detail)
   - No soil moisture (affects local weather)
   - **Impact:** Moderate improvement possible with more data

4. **One-Station Models:** Each station has independent model
   - Nearby stations have correlated weather
   - Transfer learning across stations not implemented
   - **Impact:** Could improve accuracy with ensemble

---

## 🚀 Future Improvements

### Short-term (1–3 months)

- ✅ Hourly solar radiation forecast (satellite-based)
- ✅ Ensemble combining all 7 station models
- ✅ Dynamic rain threshold tuning per season

### Medium-term (3–6 months)

- ✅ LSTM sequence-to-sequence for 21-day forecast
- ✅ Spatiotemporal transfer learning across Catalonia
- ✅ Satellite cloud cover integration

### Long-term (6+ months)

- ✅ Seasonal forecast (monthly anomalies)
- ✅ Climate model downscaling (multi-year trends)
- ✅ Probabilistic forecast (uncertainty quantification)

---

## 📥 Accessing Detailed Results

All detailed results are saved to:

```
data/predictions/
├── rainbow_forecast_final.csv        # Main 21-day forecast
├── predictions_comparation/
│   ├── onestep_*.csv                 # One-step validation
│   └── recursive_21day.csv           # Recursive forecast
├── model_analysis/
│   ├── feature_importance_*.png      # Feature ranking plots
│   ├── residuals_*.png               # Error distributions
│   └── partial_dependence_*.png      # Input-output relationships
└── comparative/
    ├── metrics_summary.csv           # Performance table
    └── comparison_plots/
        ├── error_degradation.png     # One-step vs. recursive
        └── seasonal_breakdown.png    # Summer vs. winter
```

---

**Results Status:** Updated January 2026 | **Test Period:** 2025 | **Base Models:** LightGBM 3.4+
