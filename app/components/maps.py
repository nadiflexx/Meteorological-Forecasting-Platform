"""
Geospatial visualization components using Folium.
"""

import folium
import pandas as pd
from streamlit_folium import st_folium

from src.config.settings import STATION_COORDS


def render_forecast_map(df_today: pd.DataFrame) -> None:
    """
    Renders a Folium map with weather markers for a specific date.

    Args:
        df_today (pd.DataFrame): Dataframe filtered for a single day.
                                 Must contain: 'indicativo', 'pred_tmed', 'prob_rain'.
    """
    # 1. Create Base Map (Centered on Catalonia)
    m = folium.Map(
        location=[41.6, 1.8],
        zoom_start=8,
        tiles="CartoDB positron",
        scrollWheelZoom=False,
    )

    # 2. Iterate and Add Markers
    for _, row in df_today.iterrows():
        station_code = row["indicativo"]

        # Safe coordinate retrieval with fallback
        coords = STATION_COORDS.get(
            station_code, {"lat": 41.38, "lon": 2.17, "name": station_code}
        )

        # Determine Icon based on logic
        prob_rain = row["prob_rain"]
        temp = round(row["pred_tmed"])

        # Visual Logic
        if prob_rain > 0.5:
            icon_name = "cloud-showers-heavy"
            color = "blue"
        elif row["pred_sol"] > 8.0:
            icon_name = "sun"
            color = "orange"
        else:
            icon_name = "cloud"
            color = "gray"

        # HTML Popup content
        popup_html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; text-align: center; min-width: 120px;">
            <h5 style="margin: 0 0 5px 0; color: #333;">{coords["name"]}</h5>
            <div style="font-size: 16px; font-weight: bold; color: #1e293b;">
                {temp}°C
            </div>
            <div style="font-size: 12px; color: #64748b;">
                Rain Prob: {prob_rain * 100:.0f}%
            </div>
        </div>
        """

        folium.Marker(
            location=[coords["lat"], coords["lon"]],
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"{coords['name']} ({temp}°C)",
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
        ).add_to(m)

    # 3. Render in Streamlit
    st_folium(m, width="100%", height=450, returned_objects=[])
