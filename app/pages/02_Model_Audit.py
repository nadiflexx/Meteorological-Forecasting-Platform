"""
Streamlit page for Model Auditing.
Visualizes performance metrics (MAE, R2, Scatter Plots) using the One-Step Forecast validation set.
"""

from components.charts import (
    plot_confusion_matrix,
    plot_rain_probability_hist,
    plot_scatter_vs_real,
)
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
)
import streamlit as st
from utils.data_loader import apply_custom_css, load_validation_data

from src.config.settings import FileNames, ModelConfig, Paths

st.set_page_config(
    page_title="Model Audit", page_icon=Paths.ASSETS / FileNames.LOGO, layout="wide"
)
apply_custom_css()


def calculate_metrics(df, target):
    """Calculates MAE and R2 for a regression target."""
    real_col = f"real_{target}"
    pred_col = f"pred_{target}"

    if real_col not in df.columns or pred_col not in df.columns:
        return None, None

    valid = df.dropna(subset=[real_col, pred_col])
    mae = mean_absolute_error(valid[real_col], valid[pred_col])
    r2 = r2_score(valid[real_col], valid[pred_col])

    return mae, r2


# --- MAIN UI ---

st.title("📊 AI Model Audit (2025 Validation)")
st.markdown("Technical evaluation of LightGBM model performance on the Test Set.")

df_val = load_validation_data()

if df_val is None:
    st.error("⚠️ Validation file not found. Please run pipelines first.")
    st.stop()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    ["🌡️ Temperature", "🌧️ Rain Classifier", "🌬️ Atmosphere (Wind/Sun/Hum)", "📝 Raw Data"]
)

# --- TAB 1: TEMPERATURE ---
with tab1:
    st.markdown("### Temperature Performance")

    # Metrics Row
    col1, col2, col3 = st.columns(3)
    targets = [("tmed", "Avg Temp"), ("tmin", "Min Temp"), ("tmax", "Max Temp")]

    for i, (target, label) in enumerate(targets):
        mae, r2 = calculate_metrics(df_val, target)
        with [col1, col2, col3][i]:
            st.metric(f"{label} MAE", f"{mae:.2f} °C")
            st.metric(f"{label} R²", f"{r2:.3f}")

    st.markdown("---")

    # Plots Row (3 columns now)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(
            plot_scatter_vs_real(df_val, "tmed", "Avg Temp (Tmed)", "°C"),
            width="stretch",
        )
    with c2:
        st.plotly_chart(
            plot_scatter_vs_real(df_val, "tmin", "Min Temp (Tmin)", "°C"),
            width="stretch",
        )
    with c3:
        st.plotly_chart(
            plot_scatter_vs_real(df_val, "tmax", "Max Temp (Tmax)", "°C"),
            width="stretch",
        )

# --- TAB 2: RAIN CLASSIFIER ---
with tab2:
    st.markdown("### 🌧️ Rain Classification Performance")

    if "real_prec" in df_val.columns and "pred_prob_rain" in df_val.columns:
        # 1. Calculation
        y_true = (df_val["real_prec"] > 0.1).astype(int)
        y_prob = df_val["pred_prob_rain"]
        y_pred = (y_prob > ModelConfig.RAIN_THRESHOLD).astype(int)

        auc = roc_auc_score(y_true, y_prob)
        acc = accuracy_score(y_true, y_pred)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        # 2. Metrics Row
        c1, c2, c3 = st.columns(3)
        c1.metric("ROC-AUC", f"{auc:.3f}", help="Model's ability to separate classes.")
        c2.metric(
            "Accuracy", f"{acc * 100:.1f}%", help="Percentage of total correct hits."
        )
        c3.metric(
            "Threshold", f"{ModelConfig.RAIN_THRESHOLD}", help="Decision cut-off point."
        )

        st.markdown("---")

        # 3. Visuals Row
        col_left, col_right = st.columns(2)
        with col_left:
            # Confusion Matrix Heatmap
            st.plotly_chart(plot_confusion_matrix(tn, fp, fn, tp), width="stretch")
            st.caption(
                "TN: Correct Dry days | TP: Correct Rainy days | FP: False Alarms | FN: Missed Rain."
            )

        with col_right:
            # Probability Histogram
            st.plotly_chart(plot_rain_probability_hist(df_val), width="stretch")
            st.caption(
                "This shows how well the model separates Rainy vs Dry days based on probability."
            )

    else:
        st.warning("Rain validation data missing.")

# --- TAB 3: ATMOSPHERE ---
with tab3:
    st.markdown("### 🌬️ Atmospheric Variables")

    # Metrics
    c1, c2, c3 = st.columns(3)

    with c1:
        mae, r2 = calculate_metrics(df_val, "velmedia")
        st.metric("Wind Speed MAE", f"{mae:.2f} km/h")
        st.metric("Wind R²", f"{r2:.3f}")

    with c2:
        mae, r2 = calculate_metrics(df_val, "sol")
        st.metric("Sunshine MAE", f"{mae:.2f} h")
        st.metric("Sun R²", f"{r2:.3f}")

    with c3:
        mae, r2 = calculate_metrics(df_val, "hrMedia")
        st.metric("Humidity MAE", f"{mae:.2f} %")
        st.metric("Humidity R²", f"{r2:.3f}")

    st.markdown("---")

    # Plots (3 columns)
    p1, p2, p3 = st.columns(3)

    with p1:
        st.plotly_chart(
            plot_scatter_vs_real(df_val, "velmedia", "Wind Speed", "km/h"),
            width="stretch",
        )
    with p2:
        st.plotly_chart(
            plot_scatter_vs_real(df_val, "sol", "Sunshine Hours", "h"),
            width="stretch",
        )
    with p3:
        st.plotly_chart(
            plot_scatter_vs_real(df_val, "hrMedia", "Relative Humidity", "%"),
            width="stretch",
        )

# --- TAB 4: RAW DATA ---
with tab4:
    st.markdown("### 🔍 Validation Dataset (First 100 rows)")
    st.dataframe(df_val.head(100), width="stretch")
