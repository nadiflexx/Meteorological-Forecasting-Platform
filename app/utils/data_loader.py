"""
Data Loading Utilities.
Uses centralized settings from src.config.settings.
"""

import pandas as pd
import streamlit as st

from src.config.settings import Paths


@st.cache_data(ttl=3600, show_spinner=False)
def load_rainbow_predictions() -> pd.DataFrame | None:
    file_path = Paths.PREDICTIONS / "rainbow_forecast_final.csv"

    if not file_path.exists():
        return None

    try:
        df = pd.read_csv(file_path)
        if "fecha" in df.columns:
            df["fecha"] = pd.to_datetime(df["fecha"])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_evaluation_data(filename: str) -> pd.DataFrame | None:
    file_path = Paths.PREDICTIONS / filename
    if file_path.exists():
        return pd.read_csv(file_path)
    return None


def apply_custom_css() -> None:
    css_path = Paths.ASSETS / "style.css"
    if css_path.exists():
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
