"""
🌈 Rainbow AI - Main Entry Point.

This is the landing page of the application. It handles the initial configuration,
global styling injection, the loading sequence, and the welcome dashboard.
"""

from components.loading import show_loading_with_progress
import streamlit as st
from utils.data_loader import apply_custom_css

from src.config.settings import HERO_IMAGE_URL, FileNames, Paths

# 1. Page Configuration
st.set_page_config(
    page_title="Rainbow AI",
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Global Styles
apply_custom_css()


def main() -> None:
    """Main execution flow of the application."""

    # --- LOADING LOGIC ---
    if "app_loaded" not in st.session_state:
        show_loading_with_progress()
        st.session_state.app_loaded = True
        st.rerun()

    # --- MAIN DASHBOARD CONTENT ---

    # Hero Header
    st.markdown(
        """
        <div style='text-align: center; padding: 40px 0 20px 0;'>
            <h1 style='font-size: 3.5rem; margin-bottom: 10px; font-weight: 800;'>
                Rainbow <span style='color: #7C3AED;'>AI</span>
            </h1>
            <p style='font-size: 1.2rem; color: #64748B; max-width: 600px; margin: 0 auto;'>
                Advanced Meteorological Intelligence System (2025 Forecast).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Introduction Cards (Hub Layout)
    st.subheader("📍 Explore the Modules")

    col1, col2, col3, col4 = st.columns(4)

    # --- MODULE 1: RAINBOW HUNTER ---
    with col1, st.container(border=True):
        st.markdown("### 🌈 Rainbow Hunter")
        st.markdown(
            "Physics-based prediction engine specifically calibrated to detect "
            "rainbow formation probabilities using relative humidity and solar angle."
        )
        st.markdown("<br>", unsafe_allow_html=True)

        st.page_link(
            Paths.PAGES / FileNames.RAINBOW,
            label="Launch Hunter",
            icon="🔭",
            width="stretch",
        )

    # --- MODULE 2: MODEL AUDIT ---
    with col2, st.container(border=True):
        st.markdown("### 🛠️ Model Audit")
        st.markdown(
            "Transparent evaluation of the AI models. Visualize MAE, ROC-AUC curves "
            "and scatter plots for Temperature, Wind, and Rain models."
        )
        st.markdown("<br>", unsafe_allow_html=True)

        st.page_link(
            Paths.PAGES / FileNames.AUDIT,
            label="View Analytics",
            icon="📊",
            width="stretch",
        )
    # --- MODULE 3: WEATHER FORECAST ---
    with col3, st.container(border=True):
        st.markdown("### 🌤️ Weather Forecast")
        st.markdown(
            "7-day weather forecasting dashboard with temperature trends, "
            "rain probabilities, and atmospheric conditions."
        )
        st.markdown("<br>", unsafe_allow_html=True)

        st.page_link(
            Paths.PAGES / FileNames.WEATHER,
            label="View Forecast",
            icon="⛅",
            width="stretch",
        )
    # --- MODULE 4: WEATHER & ALERTS ---
    with col4, st.container(border=True):
        st.markdown("### ❄️ Weather & Alerts")
        st.markdown(
            "General forecasting dashboard including temperature trends, rain probability, "
            "and a **Wind Chill Notification System**."
        )
        st.markdown("<br>", unsafe_allow_html=True)

        st.page_link(
            Paths.PAGES / FileNames.WINDCHILL,
            label="Setup Alerts",
            icon="🔔",
            width="stretch",
        )

    # Footer Image
    st.markdown("<br>", unsafe_allow_html=True)
    col_img_1, col_img_2, col_img_3 = st.columns([1, 2, 1])
    with col_img_2:
        st.image(
            HERO_IMAGE_URL,
            caption="Atmospheric Optical Simulation",
            width="stretch",
        )


if __name__ == "__main__":
    main()
