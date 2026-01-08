"""
PIPELINE 06: Comparative report between One-Step and Recursive Predictions
----------------------------------------------------------
Generetes metrics and graphics for ALL target variables:
[tmed, tmin, tmax, sol, hrMedia, velmedia, rain]

Compares:
1. Reality (Ground Truth)
2. One-Step Prediction (Model's short-term intelligence)
3. Recursive Prediction (Model's long-term stability)
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_absolute_error, roc_auc_score

from src.config.settings import VAR_META, FileNames, Paths
from src.utils.logger import log

# Style settings
plt.style.use("ggplot")
sns.set_theme(style="whitegrid")


def load_and_merge_data():
    """Loads and unifies the datasets of One-Step and Recursive for all target variables."""

    # 1. Load datasets
    path_onestep = Paths.PREDICTIONS / FileNames.FORECAST_ONESTEP
    path_recursive = Paths.PREDICTIONS / FileNames.FORECAST_RECURSIVE

    if not path_onestep.exists() or not path_recursive.exists():
        log.error("❌ Missing files. Execute previous pipelines first. (04 and 05)")
        return None

    df_os = pd.read_csv(path_onestep)
    df_rec = pd.read_csv(path_recursive)

    # Convert Dates
    df_os["fecha"] = pd.to_datetime(df_os["fecha"])
    df_rec["fecha"] = pd.to_datetime(df_rec["fecha"])

    # 2. Rename columns for the master merge
    # Variables to process
    targets = ["tmed", "tmin", "tmax", "sol", "hrMedia", "velmedia"]

    # Prepare One-Step (has prefix 'real_' and 'pred_')
    rename_os = {f"pred_{t}": f"{t}_onestep" for t in targets}
    rename_os["pred_prob_rain"] = "rain_onestep"

    # Prepare Recursive (has no prefix)
    rename_rec = {t: f"{t}_recursive" for t in targets}
    rename_rec["prob_rain"] = "rain_recursive"

    # Rename
    df_os = df_os.rename(columns=rename_os)
    df_rec = df_rec.rename(columns=rename_rec)

    # 3. Merge
    # Use 'real_' from one-step as the absolute truth
    merge_cols = ["fecha", "indicativo"]

    # Columns to bring from OneStep (Reales + Preds)
    cols_os = merge_cols + [
        c for c in df_os.columns if c.endswith("_onestep") or c.startswith("real_")
    ]

    # Columns to bring from Recursive (Solo Preds)
    cols_rec = merge_cols + [c for c in df_rec.columns if c.endswith("_recursive")]

    df_final = pd.merge(df_os[cols_os], df_rec[cols_rec], on=merge_cols, how="inner")

    return df_final


def generate_full_metrics(df):
    """Generete a comparative table for all target variables."""
    log.info("\n" + "=" * 80)
    log.info("📊 GLOBAL PERFORMANCE OF THE MODEL 2025 (MAE)")
    log.info("=" * 80)
    log.info(
        f"{'VARIABLE':<15} | {'ONE-STEP (Day a Day)':<20} | {'RECURSIVE (Long-Term)':<20} | {'DEGRADATION (%)':<12}"
    )
    log.info("-" * 80)

    targets = ["tmed", "tmin", "tmax", "sol", "hrMedia", "velmedia"]

    for t in targets:
        real_col = f"real_{t}"

        # Calculate MAE
        mae_os = mean_absolute_error(df[real_col], df[f"{t}_onestep"])
        mae_rec = mean_absolute_error(df[real_col], df[f"{t}_recursive"])

        # Calculate degradation (%)
        deg = ((mae_rec - mae_os) / mae_os) * 100 if mae_os > 0 else 0

        # Color output (simple)
        deg_str = f"+{deg:.0f}%"
        if deg > 100:
            deg_str = f"⚠️ {deg_str}"

        log.info(
            f"{t.upper():<15} | {mae_os:.3f} {VAR_META[t]['unit']:<14} | {mae_rec:.3f} {VAR_META[t]['unit']:<14} | {deg_str}"
        )

    # Special metric for rain (ROC-AUC)
    if "rain_onestep" in df.columns and "real_prec" in df.columns:
        # Binarizar realidad (> 0.1mm)
        y_true = (df["real_prec"] > 0.1).astype(int)

        auc_os = roc_auc_score(y_true, df["rain_onestep"])
        auc_rec = roc_auc_score(y_true, df["rain_recursive"])

        log.info("-" * 80)
        log.info(
            f"{'RAIN (AUC)':<15} | {auc_os:.3f} {'(0-1)':<14} | {auc_rec:.3f} {'(0-1)':<14} | Difference"
        )


def plot_variable_comparison(df, station_code, variable):
    """
    Generates a detailed comparative chart for a specific variable.
    Shows: Reality vs OneStep vs Recursive.
    """
    meta = VAR_META.get(variable, {"label": variable, "unit": "", "color": "gray"})

    # Filter station and sort
    df_st = df[df["indicativo"] == station_code].sort_values("fecha")

    # Take the first 60 days so it looks good (Zoom)
    df_plot = df_st.head(60).copy()

    if df_plot.empty:
        return

    plt.figure(figsize=(14, 6))

    # 1. REALITY (Black)
    if variable == "rain":
        # For rain, we paint bars of real precipitation in another axis or scale
        # We create a fake line of "It Rained" (1.0) or "It Didn't Rain" (0.0) for visual comparison
        y_real_binary = (df_plot["real_prec"] > 0.1).astype(float)
        plt.fill_between(
            df_plot["fecha"],
            0,
            y_real_binary,
            color="skyblue",
            alpha=0.3,
            label="Real rain (Yes/No)",
        )
    else:
        plt.plot(
            df_plot["fecha"],
            df_plot[f"real_{variable}"],
            label="Reality (Sensor)",
            color="black",
            linewidth=2.5,
        )

    # 2. ONE-STEP (green)
    col_os = f"{variable}_onestep"
    plt.plot(
        df_plot["fecha"],
        df_plot[col_os],
        label="One-Step Prediction (Short-Term)",
        color="green",
        alpha=0.8,
        linewidth=1.5,
    )

    # 3. RECURSIVE (Red Dotted)
    col_rec = f"{variable}_recursive"
    plt.plot(
        df_plot["fecha"],
        df_plot[col_rec],
        label="Recursive Prediction (Long-Term)",
        color="red",
        alpha=0.8,
        linestyle="--",
        linewidth=1.5,
    )

    # Details
    plt.title(
        f"Model analysis {variable.upper()}: Station {station_code} (Jan-Feb 2025)",
        fontsize=14,
    )
    plt.ylabel(f"{meta['label']} ({meta['unit']})", fontsize=12)
    plt.legend(loc="upper left" if variable != "rain" else "upper right")
    plt.grid(True, alpha=0.3)

    # Save
    filename = f"comparative_analysis_{variable}_{station_code}.png"
    output_path = Paths.PREDICTIONS / filename
    plt.savefig(output_path, dpi=150)
    plt.close()

    log.info(f"📈 Generated: {filename}")


def main():
    """Main function to execute the comparative report pipeline."""
    df = load_and_merge_data()
    if df is None:
        return

    generate_full_metrics(df)

    log.info("\nGenerating detailed charts for Pontons (0061X)...")
    targets = ["tmed", "tmin", "tmax", "sol", "hrMedia", "velmedia", "rain"]

    for t in targets:
        plot_variable_comparison(df, station_code="0061X", variable=t)

    log.info("\n✅ Process completed. Check the data/predictions folder.")


if __name__ == "__main__":
    main()
