"""
🌈 Loading Screen Component
Independent module for the Rainbow AI startup animation.
"""

import textwrap
import time

import streamlit as st
from utils.data_loader import load_image_base64

from src.config.settings import FileNames, Paths

# 1. Page Configuration
logo_path = Paths.ASSETS / FileNames.LOGO
logo_base64 = load_image_base64(logo_path)


def show_loading_with_progress() -> bool:
    """
    Displays the loading screen with staged progress bars.
    Returns: True when loading is complete.
    """
    # Check if already loaded to avoid re-running on hot-reloads
    if st.session_state.get("app_loaded", False):
        return True

    loading_container = st.empty()

    with loading_container.container():
        # Hide default elements
        st.markdown(
            """
            <style>
                .stApp > header { opacity: 0; }
                .stSidebar { display: none; }
                section[data-testid="stSidebar"] { display: none; }
            </style>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            html = f"""
            <div style='text-align: center; padding-top: 120px;'>
                <img src="data:image/png;base64,{logo_base64}"
                    alt="Rainbow AI Logo"
                    style="width:500px; height:auto; margin-bottom:20px;" />
                <p style='color: #94a3b8; font-size: 0.9rem; letter-spacing: 3px; text-transform: uppercase;'>Meteorological Intelligence System</p>
            </div>
            """

            st.markdown(textwrap.dedent(html), unsafe_allow_html=True)

            st.markdown("<br><br>", unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_text = st.empty()

            loading_stages = [
                ("🔌 Connecting to Open-Meteo & AEMET...", 15),
                ("📂 Loading processed datasets...", 30),
                ("🤖 Initializing LightGBM Models...", 50),
                ("🌡️ Integrating Physics Engine (Magnus Formula)...", 65),
                ("☔ Calculating Precipitation probabilities...", 80),
                ("🌈 Generating Rainbow Forecasts...", 90),
                ("✨ Finalizing Dashboard...", 100),
            ]

            for stage_message, progress_value in loading_stages:
                status_text.markdown(
                    f"<p style='text-align: center; color: #94a3b8; font-size: 1rem;'>{stage_message}</p>",
                    unsafe_allow_html=True,
                )
                progress_bar.progress(progress_value)
                time.sleep(0.3)

            status_text.markdown(
                "<p style='text-align: center; color: #22c55e; font-size: 1rem; font-weight: 600;'>✅ System Ready!</p>",
                unsafe_allow_html=True,
            )
            time.sleep(0.5)

    loading_container.empty()
    st.session_state.app_loaded = True
    return True
