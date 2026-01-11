"""
PIPELINE 06: COMPARATIVE FINAL REPORT
--------------------------------------------------
Generates advanced metrics (R2, MedAE, MCC) for ALL models defined in configuration,
separating Regression and Classification tasks.
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    matthews_corrcoef,
    mean_absolute_error,
    median_absolute_error,
    r2_score,
    roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config.settings import (
    SEASONS,
    VAR_META,
    FeatureConfig,
    FileNames,
    ModelConfig,
    Paths,
)
from src.utils.logger import log

# Style Configuration
plt.style.use("ggplot")
sns.set_theme(style="whitegrid")


def load_and_merge_data():
    """Dynamically loads and merges datasets based on FeatureConfig."""
    path_onestep = Paths.PREDICTIONS_COMPARATION / FileNames.FORECAST_ONESTEP
    path_recursive = Paths.PREDICTIONS_COMPARATION / FileNames.FORECAST_RECURSIVE

    if not path_onestep.exists() or not path_recursive.exists():
        log.error("❌ Missing files. Run pipelines 06 and 08 first.")
        return None

    df_os = pd.read_csv(path_onestep)
    df_rec = pd.read_csv(path_recursive)

    df_os["fecha"] = pd.to_datetime(df_os["fecha"])
    df_rec["fecha"] = pd.to_datetime(df_rec["fecha"])

    # Get targets from configuration
    targets = FeatureConfig.TARGETS

    rename_os = {}
    rename_rec = {}

    for t in targets:
        if t == "rain":
            rename_os["pred_prob_rain"] = "rain_onestep"
            rename_os["pred_is_raining"] = "rain_class_onestep"
            rename_rec["prob_rain"] = "rain_recursive"
        else:
            rename_os[f"pred_{t}"] = f"{t}_onestep"
            rename_rec[t] = f"{t}_recursive"

    df_os = df_os.rename(columns=rename_os)
    df_rec = df_rec.rename(columns=rename_rec)

    # Recalculate recursive binary class if missing
    if "rain_recursive" in df_rec.columns:
        df_rec["rain_class_recursive"] = (
            df_rec["rain_recursive"] > ModelConfig.RAIN_THRESHOLD
        ).astype(int)

    merge_cols = ["fecha", "indicativo"]

    # Columns to keep
    cols_os = merge_cols + [
        c for c in df_os.columns if "onestep" in c or c.startswith("real_")
    ]
    cols_rec = merge_cols + [c for c in df_rec.columns if "recursive" in c]

    df_final = pd.merge(df_os[cols_os], df_rec[cols_rec], on=merge_cols, how="inner")
    return df_final


def generate_full_metrics(df):
    """Generates PRO metrics table for all targets."""

    # Separate Regression and Classification targets
    reg_targets = [t for t in FeatureConfig.TARGETS if t != "rain"]
    cls_targets = ["rain"] if "rain" in FeatureConfig.TARGETS else []

    # --- 1. REGRESSION ---
    log.info("\n" + "=" * 100)
    log.info("📊 REGRESSION MODEL COMPARISON (One-Step vs Recursive)")
    log.info("=" * 100)
    header = f"{'MODEL':<10} | {'MAE':<10} | {'MedAE':<10} | {'R2 Score':<10} || {'Recur MAE':<10} | {'Degradation':<12}"
    log.info(header)
    log.info("-" * 100)

    for t in reg_targets:
        real_col = f"real_{t}"
        col_os = f"{t}_onestep"
        col_rec = f"{t}_recursive"

        # Validate existence of columns
        if (
            real_col not in df.columns
            or col_os not in df.columns
            or col_rec not in df.columns
        ):
            continue

        # Metrics One-Step
        mae_os = mean_absolute_error(df[real_col], df[col_os])
        medae = median_absolute_error(df[real_col], df[col_os])
        r2 = r2_score(df[real_col], df[col_os])

        # Metrics Recursive
        mae_rec = mean_absolute_error(df[real_col], df[col_rec])

        # Degradation
        deg = ((mae_rec - mae_os) / mae_os) * 100 if mae_os > 0 else 0
        deg_str = f"+{deg:.0f}%"

        log.info(
            f"{t.upper():<10} | {mae_os:<10.3f} | {medae:<10.3f} | {r2:<10.3f} || {mae_rec:<10.3f} | {deg_str}"
        )

    # --- 2. CLASSIFICATION ---
    if cls_targets and "rain_onestep" in df.columns and "real_prec" in df.columns:
        log.info("\n" + "=" * 100)
        log.info("🌧️  CLASSIFICATION METRICS (RAIN)")
        log.info("=" * 100)

        real_col = "real_prec"
        # Binarize Reality (> 0.1mm)
        y_true = (df[real_col] > 0.1).astype(int)
        y_prob = df["rain_onestep"]
        y_pred = df["rain_class_onestep"]

        auc = roc_auc_score(y_true, y_prob)
        f1 = f1_score(y_true, y_pred)
        mcc = matthews_corrcoef(y_true, y_pred)
        acc = accuracy_score(y_true, y_pred)

        log.info(f"   • ROC-AUC:  {auc:.3f} (Ability to distinguish dry/wet days)")
        log.info(f"   • Accuracy: {acc:.3f} (Total percentage of hits)")
        log.info(f"   • F1-Score: {f1:.3f} (Balance Precision/Recall)")
        log.info(f"   • MCC:      {mcc:.3f} (Real correlation without class bias)")

        if mcc < 0.5:
            log.info(
                f"\n   ⚠️ NOTE: An MCC of {mcc:.3f} indicates the model is conservative."
            )
            log.info(
                f"      Consider lowering RAIN_THRESHOLD (current: {ModelConfig.RAIN_THRESHOLD}) in settings.py"
            )


def plot_seasonal_grid(df, station_code, variable):
    """Generates a 2x2 grid plot (Seasonal)."""
    meta = VAR_META.get(variable, {"label": variable, "unit": "", "color": "gray"})
    df_st = df[df["indicativo"] == station_code].sort_values("fecha")

    if df_st.empty:
        return

    fig, axes = plt.subplots(2, 2, figsize=(18, 10))
    fig.suptitle(
        f"Seasonal Analysis: {meta['label']} - Station {station_code} (2025)",
        fontsize=16,
        y=0.98,
    )

    axes_flat = axes.flatten()

    for i, (season_name, months) in enumerate(SEASONS.items()):
        ax = axes_flat[i]
        df_season = df_st[df_st["fecha"].dt.month.isin(months)]

        if df_season.empty:
            ax.text(0.5, 0.5, "No Data", ha="center", va="center")
            continue

        # Real Data
        if variable == "rain":
            y_real_binary = (df_season["real_prec"] > 0.1).astype(float)
            ax.fill_between(
                df_season["fecha"],
                0,
                y_real_binary,
                color="skyblue",
                alpha=0.4,
                label="Real Rain",
            )
            # Plot Probability
            ax.plot(
                df_season["fecha"],
                df_season["rain_onestep"],
                label="One-Step Prob",
                color="green",
                alpha=0.8,
            )
            ax.plot(
                df_season["fecha"],
                df_season["rain_recursive"],
                label="Recur Prob",
                color="red",
                alpha=0.8,
                linestyle="--",
            )
            ax.set_ylim(0, 1.1)
        else:
            # Check if columns exist
            if f"real_{variable}" in df_season.columns:
                ax.plot(
                    df_season["fecha"],
                    df_season[f"real_{variable}"],
                    label="Real",
                    color="black",
                    linewidth=2,
                )

            if f"{variable}_onestep" in df_season.columns:
                ax.plot(
                    df_season["fecha"],
                    df_season[f"{variable}_onestep"],
                    label="One-Step",
                    color="green",
                    alpha=0.8,
                    linewidth=1.5,
                )

            if f"{variable}_recursive" in df_season.columns:
                ax.plot(
                    df_season["fecha"],
                    df_season[f"{variable}_recursive"],
                    label="Recursive",
                    color="red",
                    alpha=0.8,
                    linestyle="--",
                    linewidth=1.5,
                )

        ax.set_title(season_name)
        ax.set_ylabel(meta["unit"])
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=30)

        if i == 0:
            ax.legend(loc="upper left", frameon=True)

    plt.tight_layout()
    filename = f"seasonal_{variable}_{station_code}.png"
    output_path = Paths.COMPARATIVE / filename
    plt.savefig(output_path, dpi=150)
    plt.close()

    log.info(f"   📈 Generated Seasonal Grid: {filename}")


def main():
    df = load_and_merge_data()
    if df is None:
        return

    generate_full_metrics(df)

    log.info("\nGenerating seasonal plots for Pontons (0061X)...")

    for t in FeatureConfig.TARGETS:
        plot_seasonal_grid(df, station_code="0061X", variable=t)

    log.info("\n✅ Process completed. Check folder data/predictions/")


if __name__ == "__main__":
    main()
