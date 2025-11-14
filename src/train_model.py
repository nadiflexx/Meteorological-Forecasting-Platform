import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score
from sklearn.model_selection import train_test_split
import joblib, os

def build_training_data():
    """Genera datos meteorológicos simulados 2020–2024."""
    dates = pd.date_range("2020-01-01", "2024-12-31", freq="D")
    rng = np.random.default_rng(42)
    
    # Temperaturas y precipitaciones estacionales realistas
    base_temp = 14 + 8 * np.sin(2 * np.pi * (dates.dayofyear - 30) / 365)
    noise = rng.normal(0, 3, len(dates))
    tavg = base_temp + noise
    tmax = tavg + rng.normal(4, 1, len(dates))
    prcp = np.clip(np.sin(2 * np.pi * (dates.dayofyear + 90) / 365), 0, 1) * rng.exponential(2, len(dates))
    rain = (prcp > 0.5).astype(int)

    return pd.DataFrame({
        "fecha": dates,
        "tavg": tavg,
        "tmax": tmax,
        "prcp": prcp,
        "rain": rain,
        "month": dates.month,
        "dayofyear": dates.dayofyear,
        "dow": dates.dayofweek
    })

def evaluate_model(name, model, X_train, y_train, X_val, y_val, X_test, y_test):
    """Evalúa un modelo en train, validation y test."""
    results = []
    # Regresión
    if name != "rain":
        for split, X, y in [("train", X_train, y_train), ("validation", X_val, y_val), ("test", X_test, y_test)]:
            y_pred = model.predict(X)
            mae = mean_absolute_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            results.append({"variable": name, "set": split, "MAE": mae, "R2": r2})
            print(f"[{name.upper()} - {split}] MAE={mae:.3f} | R²={r2:.3f}")
    # Clasificación
    else:
        for split, X, y in [("train", X_train, y_train), ("validation", X_val, y_val), ("test", X_test, y_test)]:
            y_pred = model.predict(X)
            acc = accuracy_score(y, y_pred.round())
            results.append({"variable": name, "set": split, "accuracy": acc})
            print(f"[{name.upper()} - {split}] Accuracy={acc:.3f}")
    return results

def train_and_save_models():
    df = build_training_data()
    X = df[["month", "dayofyear", "dow"]]
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)

    all_metrics = []

    targets = {
        "tavg": RandomForestRegressor(random_state=42),
        "tmax": RandomForestRegressor(random_state=42),
        "prcp": RandomForestRegressor(random_state=42),
        "rain": RandomForestClassifier(random_state=42)
    }

    for target, model in targets.items():
        y = df[target]
        # Dividir: 70% train, 15% val, 15% test
        X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, shuffle=False)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, shuffle=False)
        
        model.fit(X_train, y_train)
        joblib.dump(model, f"{models_dir}/model_{target}.pkl")

        print(f"\n✅ Modelo {target.upper()} entrenado ({len(X_train)} train / {len(X_val)} val / {len(X_test)} test)")
        metrics = evaluate_model(target, model, X_train, y_train, X_val, y_val, X_test, y_test)
        all_metrics.extend(metrics)

    # Guardar métricas
    metrics_df = pd.DataFrame(all_metrics)
    os.makedirs("data/processed", exist_ok=True)
    metrics_df.to_csv("data/processed/metrics.csv", index=False)
    print("\n📊 Métricas completas guardadas en data/processed/metrics.csv")

if __name__ == "__main__":
    train_and_save_models()
