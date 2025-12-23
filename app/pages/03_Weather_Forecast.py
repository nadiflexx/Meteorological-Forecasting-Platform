"""
Streamlit page for General Weather Forecasting.
Displays a geospatial map and detailed weekly forecast per municipality.
"""

from components.charts import plot_weekly_temperature_trend
from components.maps import render_forecast_map
import pandas as pd
import streamlit as st
from utils.data_loader import apply_custom_css, load_rainbow_predictions

from src.config.settings import STATION_COORDS

st.set_page_config(page_title="Weather Forecast", page_icon="🌦️", layout="wide")
apply_custom_css()


# --- HELPER FUNCTIONS (Internal UI Logic) ---
def _get_weather_emoji(row: pd.Series) -> str:
    """Returns an emoji based on weather conditions."""
    if row["prob_rain"] > 0.5:
        return "🌦️" if row["pred_sol"] > 2.0 else "🌧️"
    if row["pred_sol"] > 8.0:
        return "☀️"
    if row["pred_sol"] > 4.0:
        return "⛅"
    return "☁️"


def _get_station_name(code: str) -> str:
    """Retrieves friendly name from settings."""
    return STATION_COORDS.get(code, {}).get("name", code)


# --- DATA LOADING ---
df = load_rainbow_predictions()

if df is None:
    st.error("⚠️ Data not available. Run the pipeline first.")
    st.stop()

# Date Handling
df["fecha_dt"] = pd.to_datetime(df["fecha"])
today = pd.to_datetime("today").normalize()

# Simulation Logic
min_data_date = df["fecha_dt"].min()
if today < min_data_date:
    today = min_data_date


# --- SECTION 1: GENERAL MAP ---
st.title("🌦️ Weather Forecast")
st.markdown(f"**Outlook for:** {today.strftime('%A, %B %d, %Y')}")

df_today = df[df["fecha_dt"] == today].copy()

if not df_today.empty:
    render_forecast_map(df_today)
else:
    st.warning("No data available for today's map.")

st.divider()


# --- SECTION 2: MUNICIPALITY DETAIL ---
st.subheader("📍 Detailed Municipality Forecast")

col_sel, _ = st.columns([1, 2])
with col_sel:
    # Dictionary comprehension for dropdown
    station_options = {
        code: f"{code} - {_get_station_name(code)}"
        for code in df["indicativo"].unique()
    }

    selected_code = st.selectbox(
        "Select Station:",
        options=sorted(station_options.keys()),
        format_func=lambda x: station_options[x],
    )

# Filter Data (Next 7 Days)
df_station = df[df["indicativo"] == selected_code].sort_values("fecha_dt")
df_week = df_station[df_station["fecha_dt"] >= today].head(7)

if df_week.empty:
    st.warning("No future data found for this station.")
    st.stop()


# --- SECTION 3: WEEKLY CARDS ---
# Dynamic columns based on available days (up to 7)
cols = st.columns(len(df_week))

for i, (_, day_row) in enumerate(df_week.iterrows()):
    with cols[i]:
        day_label = day_row["fecha_dt"].strftime("%a %d")
        icon = _get_weather_emoji(day_row)

        # HTML Card
        st.markdown(
            f"""
            <div style="
                text-align: center;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 12px 5px;
                background-color: #FFFFFF;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
                transition: transform 0.2s;
            ">
                <div style="font-weight: 600; font-size: 0.85rem; color: #64748B; text-transform: uppercase;">
                    {day_label}
                </div>
                <div style="font-size: 2.2rem; margin: 8px 0;">{icon}</div>
                <div style="font-weight: 700; font-size: 1.1rem; color: #1E293B;">
                    {day_row["pred_tmax"]:.0f}°
                    <span style="color: #94A3B8; font-size: 0.9rem; font-weight: 400;">
                        {day_row["pred_tmin"]:.0f}°
                    </span>
                </div>
                <div style="color: #3B82F6; font-size: 0.8rem; margin-top: 6px; font-weight: 500;">
                    💧 {day_row["prob_rain"] * 100:.0f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- SECTION 4: TREND CHART ---
st.markdown("### 📈 Weekly Trend")
fig = plot_weekly_temperature_trend(df_week)
st.plotly_chart(fig, width="stretch")


# --- SECTION 5: DAILY DRILL-DOWN ---
st.markdown("### 📋 Daily Breakdown")

# Drill-down selector
selected_day_str = st.selectbox(
    "Select day for details:",
    df_week["fecha_dt"].dt.strftime("%Y-%m-%d"),
    format_func=lambda x: pd.to_datetime(x).strftime("%A, %d %B"),
)

# Filter specific row
detail_row = df_week[df_week["fecha_dt"].astype(str) == selected_day_str].iloc[0]
station_name = _get_station_name(selected_code)

with st.expander(
    f"Full Report: {detail_row['fecha_dt'].strftime('%d %b')} {station_name}",
    expanded=True,
):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
        **Temperature Metrics:**
        - **Average:** {detail_row["pred_tmed"]:.1f} °C
        - **Maximum:** <span style='color:#EF4444; font-weight:bold'>{detail_row["pred_tmax"]:.1f} °C</span>
        - **Minimum:** <span style='color:#3B82F6; font-weight:bold'>{detail_row["pred_tmin"]:.1f} °C</span>
        - **Relative Humidity:** {detail_row.get("pred_hrMedia", 0):.0f}%
        """,
            unsafe_allow_html=True,
        )

    with col2:
        dew_point_info = ""
        if "pred_punto_rocio" in detail_row:
            dew_point_info = f"- **Dew Point:** {detail_row['pred_punto_rocio']:.1f} °C"

        st.markdown(
            f"""
        **Atmospheric Conditions:**
        - **Precipitation Probability:** {detail_row["prob_rain"] * 100:.1f}%
        - **Wind Speed:** {detail_row["pred_velmedia"] * 3.6:.1f} km/h
        - **Sun Hours:** {detail_row["pred_sol"]:.1f} h
        {dew_point_info}
        - **Rainbow Probability:** <span style='color:#7C3AED; font-weight:bold'>{detail_row["rainbow_prob"]:.1f}%</span>
        """,
            unsafe_allow_html=True,
        )

    st.info(
        "ℹ️ These predictions are generated by AI models trained on physical and historical data (AEMET/Open-Meteo)."
    )
