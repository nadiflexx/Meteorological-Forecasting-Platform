# 🖥️ Frontend Structure (Streamlit)

The application acts as the presentation layer. It is divided into three specialized pages to serve different user needs.

## 1. 🌈 Rainbow Hunter

**Goal:** The "Wow" factor. Visualizes the probability of spotting a rainbow.

- **Logic:** Reads the computed `rainbow_prob` score (0-100%).
- **Visuals:** Uses a custom **SVG Animation** (`components/visuals.py`) to draw a rainbow proportional to the probability.
- **Filters:** Allows filtering by Station and Date (defaults to Today).

## 2. 📊 Model Audit

**Goal:** Technical validation and transparency.

- **Function:** Loads the evaluation datasets (`pred_vs_real_*.csv`) generated during training.
- **Visualizations:**
  - **Scatter Plots (Plotly):** Compares Predicted vs Observed values. Ideally, points should align on the diagonal ($y=x$).
  - **Metrics:** Displays MAE (Mean Absolute Error) and Accuracy for each variable.
- **Scope:** Validates Temperature, Humidity, Solar Radiation, and Rain Classification.

## 3. 🌦️ Weather Forecast (El Temps)

**Goal:** A functional weather app for 21 municipalities.

- **Geospatial Map:** Uses `Folium` to plot stations on a map of Catalonia. Markers change icon dynamically (Sun/Rain/Cloud) based on the AI prediction.
- **Weekly Trend:** Displays a 7-day forecast graph showing the Temperature Range (Min/Max shading) and Rain probability bars.
- **Daily Detail:** A collapsible card showing specific predictions for Wind Speed, Dew Point, and exact temperatures.
