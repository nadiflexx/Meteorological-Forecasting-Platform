import pandas as pd
import joblib, numpy as np

def predict_weather_for_dates(start_date: str, end_date: str):
    dates = pd.date_range(start_date, end_date, freq="D")
    X_pred = pd.DataFrame({
        "month": dates.month,
        "dayofyear": dates.dayofyear,
        "dow": dates.dayofweek
    })
    preds = pd.DataFrame({"fecha": dates})
    for target in ["tavg", "tmax", "prcp", "rain"]:
        model = joblib.load(f"models/model_{target}.pkl")
        y_pred = model.predict(X_pred)
        preds[f"pred_{target}"] = np.round(y_pred, 2)
    preds["pred_prob_lluvia"] = np.clip(preds["pred_prcp"] / preds["pred_prcp"].max(), 0, 1).round(3)
    return preds

if __name__ == "__main__":
    df_pred = predict_weather_for_dates("2025-01-01", "2025-12-31")
    df_pred.to_csv("data/processed/predicciones_2025.csv", index=False, sep=';', decimal=',')
    print("✅ Predicciones guardadas en data/processed/predicciones_2025.csv")
