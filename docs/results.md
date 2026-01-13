# 📊 Model Results

Performance metrics obtained from the Test Set (2023-2025).

## 🏆 Accuracy Summary

| Variable                 | Metric  | Value        | Evaluation                                                                  |
| :----------------------- | :------ | :----------- | :-------------------------------------------------------------------------- |
| **Rain (Precipitation)** | ROC-AUC | **0.72**     | ✅ **Robust.** Good discrimination between dry and wet days.                |
| **Temperature (Avg)**    | MAE     | **1.19 °C**  | 🚀 **Excellent.** Very high precision.                                      |
| **Temperature (Min)**    | MAE     | **1.28 °C**  | ✅ **Very Good.**                                                           |
| **Temperature (Max)**    | MAE     | **1.65 °C**  | ✅ **Good.** Max temp is harder due to local heat bursts.                   |
| **Wind Speed**           | MAE     | **0.52 m/s** | 🚀 **Excellent.**                                                           |
| **Solar Radiation**      | MAE     | **1.53 h**   | ⚠️ **Acceptable.** Hard to predict exact hours due to cloud variability.    |
| **Relative Humidity**    | MAE     | **~7.7 %**   | ⚠️ **Acceptable.** Humidity is volatile. The model captures the trend well. |

## 📝 Interpretation

1.  **Rain Classification:** The model correctly identifies 73% of rain events. The inclusion of **Pressure** data was critical to achieving this score in the Mediterranean climate.
2.  **Temperature:** The models are highly reliable, making the "Weather Forecast" page very accurate for daily use.
3.  **Complex Variables:** Humidity and Solar Radiation have higher errors because they depend on micro-scale cloud dynamics that 24h daily data cannot fully capture. However, they are sufficient for estimating Rainbow probabilities.
