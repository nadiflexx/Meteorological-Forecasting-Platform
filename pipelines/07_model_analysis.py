"""
PIPELINE 10: MODEL ANALYSIS & EXPLAINABILITY (X-RAY)
----------------------------------------------------
Generates insights for documentation:
1. Feature Importance Plots (What did the model learn?)
2. Correlation Matrix of Input Features.
3. Residual Plots (Error distribution).
"""

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config.settings import FeatureConfig, FileNames, Paths
from src.features.transformation import FeatureEngineer
from src.utils.logger import log

# Style settings
plt.style.use("ggplot")
sns.set_theme(style="white")


def load_model(target_name):
    """Loads a specific trained model."""
    fname = (
        FileNames.MODEL_RAIN
        if target_name == "rain"
        else f"{FileNames.MODEL_PREFIX}{target_name}.pkl"
    )
    path = Paths.MODELS / fname
    if not path.exists():
        return None
    return joblib.load(path)


def plot_feature_importance(target_name, model_data):
    """Generates a bar chart with the top 20 most important features."""
    model = model_data["model"]
    feature_names = model_data["feature_names"]

    # Extract importance
    importance = model.feature_importance(importance_type="gain")
    df_imp = pd.DataFrame({"feature": feature_names, "importance": importance})
    df_imp = df_imp.sort_values(by="importance", ascending=False).head(20)

    plt.figure(figsize=(10, 8))
    sns.barplot(
        data=df_imp,
        x="importance",
        y="feature",
        palette="viridis",
        hue="feature",
        legend=False,
    )
    plt.title(f"Top 20 Feature Importance - Model: {target_name.upper()}")
    plt.xlabel("Information Gain (Importance)")
    plt.ylabel("Feature Name")
    plt.tight_layout()

    output_path = Paths.MODEL_ANALYSIS / f"analysis_importance_{target_name}.png"
    plt.savefig(output_path, dpi=150)
    plt.close()
    log.info(f"   📊 Saved Importance Plot: {output_path.name}")


def plot_correlation_heatmap(df):
    """Plots correlation matrix of the numeric features."""
    base_cols = [
        "tmed",
        "tmin",
        "tmax",
        "presion",
        "hrMedia",
        "velmedia",
        "sol",
        "nubes",
    ]
    lag_1_cols = [f"{c}_lag_1" for c in base_cols if f"{c}_lag_1" in df.columns]

    plot_cols = base_cols + lag_1_cols
    plot_cols = [c for c in plot_cols if c in df.columns]

    corr = df[plot_cols].corr()

    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr,
        mask=mask,
        cmap="coolwarm",
        vmax=1,
        vmin=-1,
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.5},
    )

    plt.title("Correlation Matrix (Input Features)")
    plt.tight_layout()

    output_path = Paths.MODEL_ANALYSIS / FileNames.CORRELATION_MATRIX
    plt.savefig(output_path, dpi=150)
    plt.close()
    log.info(f"   🔥 Saved Correlation Matrix: {output_path.name}")


def analyze_models():
    log.info("🚀 STARTING MODEL X-RAY ANALYSIS")

    # 1. LOAD DATA FOR CORRELATION ANALYSIS
    data_path = Paths.PROCESSED / FileNames.CLEAN_DATA
    df = pd.read_csv(data_path)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values(["indicativo", "fecha"])

    df_2024 = df[df["fecha"].dt.year == 2024].copy()

    log.info("⚙️ Re-generating features for analysis...")
    df_eng = df_2024.copy()
    df_eng = FeatureEngineer.add_time_cyclicality(df_eng)
    df_eng = FeatureEngineer.add_wind_components(df_eng)

    for col in FeatureConfig.LAG_COLS:
        if col in df_eng.columns:
            for lag in FeatureConfig.LAGS:
                df_eng[f"{col}_lag_{lag}"] = df_eng.groupby("indicativo")[col].shift(
                    lag
                )

    # PLOT 1: Correlation Matrix
    plot_correlation_heatmap(df_eng)

    # 2. ANALYZE EACH MODEL
    targets = ["tmed", "tmin", "tmax", "rain", "sol", "hrMedia", "velmedia"]

    for target in targets:
        model_data = load_model(target)
        if model_data:
            # PLOT 2: Feature Importance
            plot_feature_importance(target, model_data)
        else:
            log.warning(f"⚠️ Model {target} not found. Skipping.")

    log.info("✅ Analysis Completed. Check data/predictions folder.")


if __name__ == "__main__":
    analyze_models()
