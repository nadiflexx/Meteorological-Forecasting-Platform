"""
Streamlit page for the "Rainbow Hunter" feature.
Main dashboard for visualizing rainbow probabilities.
"""

from datetime import date

from components.visuals import render_rainbow_animation
import pandas as pd
import streamlit as st
from utils.data_loader import apply_custom_css, load_rainbow_predictions

from src.config.settings import STATION_COORDS, FileNames, Paths

# ---------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Rainbow Hunter",
    layout="wide",
    page_icon=Paths.ASSETS / FileNames.LOGO,
)
apply_custom_css()

# ---------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------
st.title("🌈 Rainbow Hunter")
st.markdown("Physics-based probability forecast for rainbow sightings by station.")

# ---------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------
df = load_rainbow_predictions()

if df is None:
    st.error(
        "⚠️ No data available. Please run the training pipeline first:\n"
        "`uv run pipelines/03_train_model.py`"
    )
    st.stop()


# Auxiliar function to set the select label with format ID + " " + "Station_name"
def format_station_label(station_id):
    # Check the dictionary
    info = STATION_COORDS.get(station_id)
    if info:
        return f"{station_id} {info['name']}"
    return station_id


# ---------------------------------------------------------------------
# SIDEBAR CONFIGURATION
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Configuration")

    # 1. Station selection
    stations = sorted(df["indicativo"].unique())
    selected_station = st.selectbox(
        "Weather Station",
        stations,
        format_func=format_station_label,
    )

    df_station = df[df["indicativo"] == selected_station].copy()

    # 2. Date handling
    df_station["fecha_dt"] = pd.to_datetime(df_station["fecha"])
    df_station["fecha_date"] = df_station["fecha_dt"].dt.date

    current_year = date.today().year - 1  # Show 2025 data in 2026

    # Filter to current year onwards (should be 2025 or later) (Today is 2026) change te function to get 2025 aswell
    df_future = df_station[df_station["fecha_dt"].dt.year >= current_year]

    if df_future.empty:
        st.warning(f"⚠️ No predictions found for {current_year}+. Showing full history.")
        available_dates = sorted(df_station["fecha_date"].unique(), reverse=True)
    else:
        available_dates = sorted(df_future["fecha_date"].unique(), reverse=True)

    # 3. Date selector
    today = date.today()
    default_index = 0

    if today in available_dates:
        default_index = available_dates.index(today)

    selected_date = st.selectbox(
        "Prediction Date",
        available_dates,
        index=default_index,
        help="Select a date to view specific atmospheric conditions.",
    )

# ---------------------------------------------------------------------
# SELECT ROW FOR CURRENT SELECTION
# ---------------------------------------------------------------------
try:
    row = df_station[df_station["fecha_date"] == selected_date].iloc[0]
except IndexError:
    st.error("Data not found for the selected date.")
    st.stop()

# ---------------------------------------------------------------------
# DASHBOARD LAYOUT
# ---------------------------------------------------------------------
col_main, col_metrics = st.columns([1.5, 1])

# ---------------------------------------------------------------------
# MAIN VISUAL
# ---------------------------------------------------------------------
with col_main:
    render_rainbow_animation(row["rainbow_prob"])

    prob = row["rainbow_prob"]

    if prob >= 60:
        st.success(
            f"### 🚀 HIGH PROBABILITY ({prob}%)!\n"
            "Expect showers with sun breaks. **Get your camera ready!**"
        )
    elif prob >= 30:
        st.warning(
            f"### ⛅ MEDIUM PROBABILITY ({prob}%)\n"
            "Unstable conditions. A sighting is possible."
        )
    else:
        st.info(
            f"### 💤 LOW PROBABILITY ({prob}%)\n"
            "Sky is either too clear or too overcast."
        )

# ---------------------------------------------------------------------
# METRICS PANEL
# ---------------------------------------------------------------------
with col_metrics:
    st.subheader("Atmospheric Factors")

    col_a, col_b = st.columns(2)
    col_a.metric(
        "Rain Chance",
        f"{row['prob_rain'] * 100:.0f}%",
        delta="Probability",
    )
    col_b.metric(
        "Insolation",
        f"{row['pred_sol']:.1f} h",
        delta="Hours of Sun",
    )

    col_c, col_d = st.columns(2)
    col_c.metric(
        "Temperature",
        f"{row['pred_tmed']:.1f}°C",
        delta="Avg Temp",
    )

    # Humidity / Dew Point context
    hum_val = row.get("pred_hrMedia", 0)

    if "pred_punto_rocio" in row:
        dew_point = row["pred_punto_rocio"]
        hum_help = f"Dew Point: {dew_point:.1f}°C"
    else:
        hum_help = f"{hum_val:.0f}%"

    hum_text = "High" if hum_val > 70 else "Medium" if hum_val > 40 else "Low"

    col_d.metric("Humidity", hum_text, help=hum_help)

    st.markdown("---")
    st.caption(f"Forecast for **{selected_date}** at **{selected_station}**.")
