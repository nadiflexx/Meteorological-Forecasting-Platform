"""
🌈 Rainbow AI - Main Entry Point.

This is the landing page of the application. It handles the initial configuration,
global styling injection, the loading sequence, and the welcome dashboard.
"""

from components.loading import show_loading_with_progress
import streamlit as st
from utils.data_loader import apply_custom_css

from src.config.settings import HERO_IMAGE_URL


def setup_page_config() -> None:
    """
    Configures the Streamlit page metadata.
    Must be the first Streamlit command run in the script.
    """
    st.set_page_config(
        page_title="Rainbow AI",
        page_icon="🌈",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_hero_section() -> None:
    """Renders the main title and subtitle using custom HTML."""
    st.markdown(
        """
        <div style='text-align: center; padding: 40px 0 30px 0;'>
            <h1 style='font-size: 3.5rem; margin-bottom: 10px; font-weight: 800;'>
                Rainbow <span style='color: #7C3AED;'>AI</span>
            </h1>
            <p style='font-size: 1.2rem; color: #64748B; max-width: 600px; margin: 0 auto;'>
                Advanced Artificial Intelligence System for the prediction
                of optical meteorological phenomena and atmospheric analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview_image() -> None:
    """Renders the central hero image with layout constraints."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.image(
            HERO_IMAGE_URL,
            caption="Atmospheric Optics Simulation",
            width="stretch",
        )


def render_features_section() -> None:
    """Renders the feature description and call-to-action."""
    st.markdown("---")

    col_text, col_info = st.columns([2, 1])

    with col_text:
        st.markdown(
            """
            ### 🚀 System Capabilities

            This professional dashboard empowers meteorologists and enthusiasts to:

            *   **🌈 Forecast Rainbows:** 24-hour physics-based probability predictions.
            *   **🌧️ Analyze Precipitation:** Calibrated LightGBM models for rain detection.
            *   **🌡️ Audit Metrics:** Technical review of Temperature, Humidity, and Solar radiation models.
            """
        )

    with col_info:
        st.info(
            """
            **💡 System Status**

            - **Data Source:** AEMET OpenData & Open-Meteo API.
            - **Update Frequency:** Daily at 06:00 UTC.
            - **Model:** Gradient Boosting (LightGBM).
            """
        )

    st.success("👈 **Navigate using the sidebar menu to start.**")


def main() -> None:
    """Main execution flow of the application."""

    # 1. Page Setup
    setup_page_config()

    # 2. Loading Animation (Blocks execution until finished)
    if not show_loading_with_progress():
        return

    # 3. Global Styles
    apply_custom_css()

    # 4. Landing Page Content
    render_hero_section()
    render_overview_image()
    render_features_section()


if __name__ == "__main__":
    main()
