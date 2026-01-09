"""
PIPELINE 09: COMPARATIVE FINAL REPORT (SEASONAL)
------------------------------------------------
Generates metrics and SEASONAL PLOTS (4 seasons per variable).

Compares:
1. Ground Truth (Real)
2. One-Step Prediction (Short-term Intelligence)
3. Recursive Prediction (Long-term Stability)
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_absolute_error, roc_auc_score

from src.config.settings import SEASONS, VAR_META, FileNames, Paths
from src.utils.logger import log

plt.style.use("ggplot")
sns.set_theme(style="whitegrid")


def load_and_merge_data():
    """Loads and merges datasets."""
    path_onestep = Paths.PREDICTIONS / FileNames.FORECAST_ONESTEP
    path_recursive = Paths.PREDICTIONS / FileNames.FORECAST_RECURSIVE

    if not path_onestep.exists() or not path_recursive.exists():
        log.error("❌ Missing files. Run pipelines 06 and 08 first.")
        return None

    df_os = pd.read_csv(path_onestep)
    df_rec = pd.read_csv(path_recursive)

    df_os["fecha"] = pd.to_datetime(df_os["fecha"])
    df_rec["fecha"] = pd.to_datetime(df_rec["fecha"])

    targets = ["tmed", "tmin", "tmax", "sol", "hrMedia", "velmedia"]

    rename_os = {f"pred_{t}": f"{t}_onestep" for t in targets}
    rename_os["pred_prob_rain"] = "rain_onestep"

    rename_rec = {t: f"{t}_recursive" for t in targets}
    rename_rec["prob_rain"] = "rain_recursive"

    df_os = df_os.rename(columns=rename_os)
    df_rec = df_rec.rename(columns=rename_rec)

    merge_cols = ["fecha", "indicativo"]
    cols_os = merge_cols + [
        c for c in df_os.columns if c.endswith("_onestep") or c.startswith("real_")
    ]
    cols_rec = merge_cols + [c for c in df_rec.columns if c.endswith("_recursive")]

    df_final = pd.merge(df_os[cols_os], df_rec[cols_rec], on=merge_cols, how="inner")
    return df_final


def generate_full_metrics(df):
    """Generates metric table in console."""
    log.info("\n" + "=" * 80)
    log.info("📊 GLOBAL PERFORMANCE COMPARISON 2025 (MAE)")
    log.info("=" * 80)
    log.info(
        f"{'VARIABLE':<15} | {'ONE-STEP (Daily)':<20} | {'RECURSIVE (Blind)':<20} | {'DEGRADATION':<12}"
    )
    log.info("-" * 80)

    targets = ["tmed", "tmin", "tmax", "sol", "hrMedia", "velmedia"]

    for t in targets:
        real_col = f"real_{t}"
        mae_os = mean_absolute_error(df[real_col], df[f"{t}_onestep"])
        mae_rec = mean_absolute_error(df[real_col], df[f"{t}_recursive"])
        deg = ((mae_rec - mae_os) / mae_os) * 100 if mae_os > 0 else 0
        deg_str = f"+{deg:.0f}%"
        if deg > 100:
            deg_str = f"⚠️ {deg_str}"

        log.info(
            f"{t.upper():<15} | {mae_os:.3f} {VAR_META[t]['unit']:<14} | {mae_rec:.3f} {VAR_META[t]['unit']:<14} | {deg_str}"
        )

    if "rain_onestep" in df.columns and "real_prec" in df.columns:
        y_true = (df["real_prec"] > 0.1).astype(int)
        auc_os = roc_auc_score(y_true, df["rain_onestep"])
        auc_rec = roc_auc_score(y_true, df["rain_recursive"])
        log.info("-" * 80)
        log.info(
            f"{'RAIN (AUC)':<15} | {auc_os:.3f} {'(0-1)':<14} | {auc_rec:.3f} {'(0-1)':<14} | Difference"
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

        # 1. REAL
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
        else:
            ax.plot(
                df_season["fecha"],
                df_season[f"real_{variable}"],
                label="Real",
                color="black",
                linewidth=2,
            )

        # 2. ONE-STEP
        ax.plot(
            df_season["fecha"],
            df_season[f"{variable}_onestep"],
            label="One-Step",
            color="green",
            alpha=0.8,
            linewidth=1.5,
        )

        # 3. RECURSIVE
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
    output_path = Paths.PREDICTIONS / filename
    plt.savefig(output_path, dpi=150)
    plt.close()

    log.info(f"   📈 Generated Seasonal Grid: {filename}")


def main():
    df = load_and_merge_data()
    if df is None:
        return

    generate_full_metrics(df)

    log.info("\nGenerating seasonal plots for Pontons (0061X)...")
    targets = ["tmed", "tmin", "tmax", "sol", "hrMedia", "velmedia", "rain"]

    for t in targets:
        plot_seasonal_grid(df, station_code="0061X", variable=t)

    log.info("\n✅ Process completed. Check folder data/predictions/")


if __name__ == "__main__":
    main()
