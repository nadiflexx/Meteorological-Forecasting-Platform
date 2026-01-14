# 🧠 Machine Learning Logic & Feature Engineering

## Overview

This document explains the feature engineering strategy, the 7 LightGBM models, rainbow probability heuristic, and wind chill calculations.

---

## 🔬 Feature Engineering Strategy

### Input Variables (AEMET Raw Data)

| Variable       | Unit  | Description                  | Source     |
| -------------- | ----- | ---------------------------- | ---------- |
| **Tmed**       | °C    | Daily mean temperature       | AEMET      |
| **Tmin**       | °C    | Daily minimum temperature    | AEMET      |
| **Tmax**       | °C    | Daily maximum temperature    | AEMET      |
| **Sol**        | Hours | Daily sunshine duration      | AEMET      |
| **HRMedia**    | %     | Daily mean relative humidity | AEMET      |
| **VelMedia**   | m/s   | Daily mean wind speed        | AEMET      |
| **Prec**       | mm    | Daily precipitation          | AEMET      |
| **Pressure**   | hPa   | Atmospheric pressure         | Open-Meteo |
| **CloudCover** | %     | Cloud coverage               | Open-Meteo |

### Feature Types

#### 1️⃣ Lag Features

Captures temporal dependencies (what happened in prior days).

```
Lags: [1, 2, 7] days

Example: T-1 (yesterday's mean temperature)
         T-2 (two days ago)
         T-7 (same day last week)

Applied to all 6 weather variables (Tmed, Tmin, Tmax, Sol, HRMedia, VelMedia)

Total lag features: 3 lags × 6 variables = 18 features
```

**Why 7 days?** Captures weekly cyclicity (e.g., weather patterns repeat ~weekly)

#### 2️⃣ Rolling Window Features

Aggregates trends over multiple days.

```
Windows: [3, 7, 14] days (mean)

Example: 3-day mean temperature (smooths daily noise)
         7-day rolling humidity (captures moisture trends)
         14-day rolling wind (long-term wind patterns)

Applied to all 6 weather variables

Total rolling features: 3 windows × 6 variables = 18 features
```

**Why rolling?** Captures momentum (e.g., warming trend, drying trend)

#### 3️⃣ Cyclical Features

Encodes seasonal and annual patterns without artificial discontinuities.

```
Using sin/cos encoding:

Day-of-Year: sin(2π × day / 365), cos(2π × day / 365)
  └─ Captures seasonal pattern (winter ≠ summer)

Month: sin(2π × month / 12), cos(2π × month / 12)
  └─ Captures long-term seasonal transitions

Total cyclical features: 2 × 2 = 4 features
```

**Why sin/cos?** Avoids discontinuity at year boundary (e.g., Dec 31 → Jan 1)

#### 4️⃣ Physics Features

Derived from atmospheric equations.

```
Magnus Formula (Dew Point from Temperature & Humidity):
  es = 6.11 × exp((17.27 × T) / (T + 237.7))    [Saturation vapor pressure]
  e = (RH / 100) × es                           [Actual vapor pressure]
  Td = (237.7 × ln(e/6.11)) / (17.27 - ln(e/6.11))

Vapor Pressure Deficit (VPD):
  VPD = es - e    [Water stress indicator]

Total physics features: ~3–5 features
```

**Why physics?** Models learn atmospheric relationships better with domain-informed features

#### 5️⃣ Target Feature Encoding

For rain classifier:

- **Binary encoding:** 0 (dry day, Prec < 1 mm), 1 (rainy day, Prec ≥ 1 mm)
- **Threshold:** Configurable in `src/config/settings.py` → `ModelConfig.RAIN_THRESHOLD`

### Summary: 27 Total Features

```
Lag Features:        18 (3 lags × 6 variables)
Rolling Features:    18 (3 windows × 6 variables)
Cyclical Features:    4 (day-of-year + month, sin/cos)
Physics Features:     3 (Magnus, VPD, etc.)
────────────────────────────────────────
Total:              ~27–30 features per observation
```

---

## 🤖 The 7 LightGBM Models

### Model Architecture

All models use **LightGBM** (Light Gradient Boosting Machine):

- Fast training (~seconds per model)
- Native handling of missing values
- Feature importance built-in
- No scaling required (tree-based)

### Model 1: Rain Classifier (Binary)

**Target:** Precipitation presence (dry vs. rainy)

```
Input:  27 features (lags, rolling, cyclical, physics)
Output: P(rain) ∈ [0, 1]
Type:   Binary classification

Hyperparameters (from src/config/settings.py):
  num_leaves: 31
  learning_rate: 0.1
  n_estimators: 100
  early_stopping_rounds: 10

Decision Threshold: ConfigModel.RAIN_THRESHOLD (default 0.3)
  - P(rain) > 0.3 → "Rainy day"
  - P(rain) ≤ 0.3 → "Dry day"

Performance (Test 2025):
  ROC-AUC: 0.72 ✅
  Precision: 0.68
  Recall: 0.64
```

**Interpretation:** 72% discrimination between rainy/dry days (good, not perfect)

---

### Models 2–4: Temperature Regressors

#### Model 2: Mean Temperature (Tmed)

```
Input:  27 features
Output: Tmed ∈ [-10, 50] °C
Type:   Regression

Performance (Test 2025):
  MAE:  1.19°C  🚀 Excellent
  RMSE: 1.58°C
  R²:   0.89
```

#### Model 3: Minimum Temperature (Tmin)

```
Input:  27 features
Output: Tmin ∈ [-15, 40] °C
Type:   Regression

Performance (Test 2025):
  MAE:  1.28°C  ✅ Very good
  RMSE: 1.71°C
  R²:   0.87
```

#### Model 4: Maximum Temperature (Tmax)

```
Input:  27 features
Output: Tmax ∈ [-5, 55] °C
Type:   Regression

Performance (Test 2025):
  MAE:  1.65°C  ✅ Good
  RMSE: 2.20°C
  R²:   0.83

Note: Tmax is harder to predict (influenced by clouds, local microclimates)
```

---

### Models 5–7: Atmosphere Regressors

#### Model 5: Solar Radiation (Sol)

```
Input:  27 features
Output: Sol ∈ [0, 14] hours
Type:   Regression

Performance (Test 2025):
  MAE:  1.53 hours  ⚠️ Acceptable
  RMSE: 2.10 hours
  R²:   0.71

Challenge: Cloud cover highly variable sub-daily; daily aggregation loses detail
```

#### Model 6: Relative Humidity (HRMedia)

```
Input:  27 features
Output: HRMedia ∈ [20, 100] %
Type:   Regression

Performance (Test 2025):
  MAE:  ~7.7%  ⚠️ Acceptable
  RMSE: 10.2%
  R²:   0.68

Challenge: Humidity volatile; depends on convection, wind shifts, dew cycles
```

#### Model 7: Wind Speed (VelMedia)

```
Input:  27 features
Output: VelMedia ∈ [0, 15] m/s
Type:   Regression

Performance (Test 2025):
  MAE:  0.52 m/s  🚀 Excellent
  RMSE: 0.79 m/s
  R²:   0.85

Note: Wind patterns more predictable (synoptic-scale meteorology)
```

---

## 🌈 Rainbow Probability Heuristic

### Concept

A rainbow requires three conditions:

1. **Rain:** Precipitation in the air
2. **Sun:** Light from behind the observer (sun low in sky)
3. **Humidity:** High moisture content

### Formula

```
Rainbow Score = Rain Score × Sun Score × Humidity Factor

Where:
  Rain Score       = P(rain) from Model 1 (classifier output)
  Sun Score        = f(solar radiation, time of day)
                   = Sol / 12  (normalize to max 12 hours)
  Humidity Factor  = HR / 100  (normalize relative humidity)

Final Rainbow Probability ∈ [0, 1]
```

### Implementation

```python
# src/modeling/rainbow.py

def calculate_rainbow_probability(
    rain_score: float,      # P(rain) ∈ [0, 1]
    solar_hours: float,     # Sol ∈ [0, 14]
    humidity: float         # HR ∈ [0, 100]
) -> float:
    sun_score = min(solar_hours / 12, 1.0)
    humidity_factor = humidity / 100

    rainbow_prob = rain_score * sun_score * humidity_factor
    return min(rainbow_prob, 1.0)  # Clip to [0, 1]
```

### Interpretation

| Rainbow Prob | Likelihood    | Appearance                      |
| ------------ | ------------- | ------------------------------- |
| **> 0.7**    | **Very High** | Primary + secondary arc visible |
| **0.5–0.7**  | **High**      | Primary arc clear               |
| **0.3–0.5**  | **Moderate**  | Partial arc or faint            |
| **0.1–0.3**  | **Low**       | Rare, poor conditions           |
| **< 0.1**    | **Very Low**  | Unlikely                        |

### Example Scenario

```
Day: 2025-06-21, Station: Barcelona

Model Outputs:
  P(rain) = 0.65  (moderately rainy afternoon)
  Sol = 10 hours  (sunny morning, cloudy afternoon)
  HR = 78%        (humid after rain)

Calculation:
  Sun Score = 10 / 12 = 0.833
  Humidity Factor = 78 / 100 = 0.78
  Rainbow Prob = 0.65 × 0.833 × 0.78 = 0.43  ← Moderate probability

  Interpretation: Good chance of rainbow if positioned correctly (sun behind you)
```

---

## ❄️ Wind Chill & Heat Index Calculations

### Why Three Formulas?

Different formulas apply to different temperature ranges:

- **Wind Chill:** Applies when T < 10°C (cooling from wind + low temp)
- **Heat Index:** Applies when T > 25°C (warming from humidity + high temp)
- **Standard:** Applies when 10°C ≤ T ≤ 25°C (no extreme effect)

### Formula 1: Standard Wind Chill (T < 10°C)

```
WC = 13.12 + 0.6215×T - 11.37×V^0.16 + 0.3965×T×V^0.16

Where:
  T = Temperature (°C)
  V = Wind speed (km/h)  [convert m/s: multiply by 3.6]
  WC = Apparent temperature (°C)

Physical interpretation:
  - Wind accelerates heat loss from skin
  - Wind chill < actual temperature (feels colder)

Example:
  T = 5°C, V = 20 km/h
  WC = 13.12 + 0.6215×5 - 11.37×20^0.16 + 0.3965×5×20^0.16
     ≈ -3.2°C  (feels 8°C colder!)
```

### Formula 2: Heat Index (T > 25°C)

```
HI = c1 + c2×T + c3×RH + c4×T×RH + c5×T² + c6×RH² + ...
   (Rothfusz regression, 8-term polynomial)

Where:
  T = Temperature (°F)  [convert °C: T_F = T_C × 9/5 + 32]
  RH = Relative humidity (%)
  HI = Apparent temperature (°F)

Physical interpretation:
  - High humidity reduces evaporative cooling
  - Heat index > actual temperature (feels hotter)

Example:
  T = 30°C (86°F), RH = 75%
  HI ≈ 38°C (100°F)  (feels 8°C hotter!)
```

### Formula 3: Steadman Formula (10°C ≤ T ≤ 25°C)

```
AT = T + 0.33×VP - 0.70×V - 4.00

Where:
  T = Temperature (°C)
  VP = Vapor pressure (hPa)
  V = Wind speed (m/s)
  AT = Apparent temperature (°C)

Transition zone: Blends cooling + humidity effects
```

### Implementation

```python
# src/modeling/wind_chill.py

def calculate_apparent_temperature(
    temp_c: float,          # Temperature (°C)
    humidity: float,        # Relative humidity (%)
    wind_speed_ms: float    # Wind speed (m/s)
) -> dict:
    """Returns apparent temperatures from all 3 formulas + selected recommendation"""

    wc = wind_chill_formula(temp_c, wind_speed_ms)        # Cold
    hi = heat_index_rothfusz(temp_c, humidity)             # Hot
    st = steadman_formula(temp_c, humidity, wind_speed_ms) # Moderate

    # Select formula based on temperature
    if temp_c < 10:
        selected = wc
    elif temp_c > 25:
        selected = hi
    else:
        selected = st

    return {
        'wind_chill': wc,
        'heat_index': hi,
        'steadman': st,
        'recommended': selected
    }
```

### Use Cases

| Scenario                     | Apparent Temp   | Impact              |
| ---------------------------- | --------------- | ------------------- |
| **Winter:** T=0°C, V=30 km/h | WC = -15°C      | Frostbite risk ⚠️   |
| **Summer:** T=35°C, RH=80%   | HI = 50°C       | Heat stroke risk ⚠️ |
| **Spring:** T=15°C, V=10 m/s | Steadman ≈ 12°C | Jacket recommended  |

---

## ⚙️ Configuration & Tuning

All hyperparameters are defined in **src/config/settings.py**:

```python
class ModelConfig:
    # LightGBM hyperparameters
    NUM_LEAVES = 31
    LEARNING_RATE = 0.1
    N_ESTIMATORS = 100
    EARLY_STOPPING_ROUNDS = 10

    # Data split
    TRAIN_END_YEAR = 2023
    VAL_YEAR = 2024
    TEST_YEAR = 2025

    # Rain classification
    RAIN_THRESHOLD = 0.3  # Adjust: 0.2 (more sensitive), 0.4 (stricter)

class FeatureConfig:
    LAG_DAYS = [1, 2, 7]
    ROLLING_WINDOWS = [3, 7, 14]
    CYCLICAL_FEATURES = ['dayofyear', 'month']
```

### Tuning Tips

| Parameter          | Effect                                                     | Recommendation |
| ------------------ | ---------------------------------------------------------- | -------------- |
| **RAIN_THRESHOLD** | Higher → fewer rain predictions (higher precision)         | Try 0.3–0.5    |
| **NUM_LEAVES**     | Higher → deeper trees (more flexible, risk of overfitting) | 20–63          |
| **LEARNING_RATE**  | Lower → slower learning (better generalization)            | 0.05–0.2       |
| **LAG_DAYS**       | Add more lags → capture longer dependencies                | [1,2,7,14,30]  |

---

## 🔮 Extension Ideas

1. **Seasonal Model Ensemble**

   - Separate models for summer vs. winter
   - Accounts for seasonal weather pattern differences

2. **Multi-Station Transfer Learning**

   - Train on all 21 stations jointly
   - Share patterns across geography

3. **Ensemble Stacking**

   - Meta-model that learns to combine 7 predictions
   - Potentially lower error

4. **Autoregressive LSTM**
   - Sequence-to-sequence for 21-day forecast
   - Captures long-range dependencies better than lags

---

**ML Logic Status:** Production-Ready | **Last Updated:** January 2026
