# 🧠 Logic & Models

The system trains **7 distinct Machine Learning models** using **LightGBM** (Gradient Boosting).

## 1. Feature Engineering strategy

Instead of raw data, we feed the models with context:

- **Temporal Context:** Lags (t-1, t-2) and Rolling Means (3-day average).
- **Cyclical Time:** Months are encoded as Sine/Cosine waves to capture seasonality.
- **Physical Context:** We include **Atmospheric Pressure** and **Cloud Cover** (from Open-Meteo) to help the model understand storm fronts.

## 2. The Models

| Variable                        | Model Type | Key Features                                          |
| :------------------------------ | :--------- | :---------------------------------------------------- |
| **Rain**                        | Classifier | Pressure Trend (`pres_diff`), Cloud Cover, Past Rain. |
| **Temperature (Avg, Min, Max)** | Regressor  | Day of Year (Seasonality), Solar Radiation.           |
| **Solar Radiation**             | Regressor  | Cloud Cover, Seasonality.                             |
| **Humidity**                    | Regressor  | Pressure, Wind Direction, Clouds.                     |
| **Wind Speed**                  | Regressor  | Pressure Gradients, Seasonality.                      |

## 3. Rainbow Heuristic

The "Rainbow Probability" is not a direct ML output, but a derived score:

$$ P = P(Rain) \times Score(Sun) \times Factor(Humidity) $$

- **P(Rain):** Must be high (but not 100%, which implies total overcast).
- **Score(Sun):** Ideal is 4-10 hours (Mixed sun/rain).
- **Factor(Humidity):** Penalizes dry air (<40%) which evaporates droplets.
