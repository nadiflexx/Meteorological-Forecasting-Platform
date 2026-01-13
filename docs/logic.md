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

## 4. Wind Chill Engine

Apparent temperature is calculated _after_ the ML predictions, combining three formulas based on conditions:

1.  **Standard Wind Chill:** Used when $T < 10°C$ and Wind $> 4.8 km/h$.
    $$ WC = 13.12 + 0.6215T - 11.37V^{0.16} + 0.3965TV^{0.16} $$
2.  **Heat Index (Rothfusz):** Used when $T > 26°C$. Accounts for humidity making heat feel oppressive.
3.  **Steadman:** Used for mild temperatures.
