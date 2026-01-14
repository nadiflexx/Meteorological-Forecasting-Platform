# 📱 Frontend: Streamlit Application Structure

## Overview

The Rainbow AI dashboard is built with **Streamlit**, a Python framework for rapid interactive application development. It provides 4 specialized pages for different user personas.

---

## 🎯 User Personas & Pages

### 👨‍🌾 Persona 1: Farmer / Outdoor Enthusiast

**Goal:** _"When will the rainbow appear?"_

### Page 1: 🌈 Rainbow Hunter

**URL:** `localhost:8501` (default landing page)

**Purpose:** Interactive rainbow probability detector with real-time forecast

**Features:**

- **📍 Station Selector**

  - Dropdown menu of 21 Catalan stations
  - Geospatial map showing selected station location

- **📊 Rainbow Probability Visualization**

  - Large SVG gauge showing probability [0–100%]
  - Color coding: Red (0%) → Yellow (50%) → Green (100%)
  - Real-time updates from model predictions

- **📅 21-Day Rainbow Forecast**

  - Calendar heatmap showing daily probabilities
  - Darker green = higher probability
  - Hover to see exact value and conditions

- **🔍 Detailed Day Breakdown**
  - Expandable cards per day
  - Shows: Rain score, Sun hours, Humidity, Combined probability
  - Tips: _"Best rainbow time: 6–8 PM on sunny rainy days"_

**Data Flow:**

```
User selects station
          ↓
Fetch latest forecast from data/predictions/rainbow_forecast_final.csv
          ↓
Calculate rainbow probability = rain_score × sun_score × humidity_factor
          ↓
Render gauge + calendar heatmap
          ↓
Display condition breakdown
```

---

### 📊 Persona 2: Data Analyst / Meteorologist

**Goal:** _"How accurate are the models?"_

### Page 2: 🔬 Model Audit

**URL:** `localhost:8501/01_Rainbow_Hunter` → Navigate to **Model Audit**

**Purpose:** Performance analysis, error assessment, and model validation

**Features:**

- **📈 Scatter Plots: Actual vs. Predicted**

  - One plot per variable (7 total: rain, tmed, tmin, tmax, sol, hr, vel)
  - X-axis: Actual values (from test set 2025)
  - Y-axis: Predicted values (from models)
  - Color: Prediction error magnitude (red = large error)
  - Perfect model = diagonal line

- **📊 Performance Metrics Table**

  ```
  | Variable | MAE | RMSE | R² | ROC-AUC |
  |----------|-----|------|----|----|
  | Rain     | —   | —    | — | 0.72 |
  | Tmed     | 1.19°C | 1.58 | 0.89 | — |
  | ...      | ... | ... | ... | ... |
  ```

- **📍 Error Distribution by Station**

  - Violin plots showing error spread per location
  - Identifies stations with systematic bias

- **🔍 Seasonal Performance**
  - Error comparison: Winter vs. Summer vs. Spring vs. Fall
  - Identifies seasonal challenges

**Data Flow:**

```
Load test predictions (from Pipeline 04)
          ↓
Compare with actual 2025 values
          ↓
Compute MAE, RMSE, R², ROC-AUC
          ↓
Render scatter plots + metrics
          ↓
Display error distributions
```

---

### 🌍 Persona 3: Weather Forecaster

**Goal:** _"What's the 21-day forecast?"_

### Page 3: 🗺️ Weather Forecast

**URL:** `localhost:8501/03_Weather_Forecast` → Navigate to **Weather Forecast**

**Purpose:** Interactive 21-day forecast visualization with geospatial maps

**Features:**

- **🗺️ Forecast Map**

  - Folium map showing all 21 stations in Catalonia
  - Station markers color-coded by selected variable
  - Example: Red (hot) ↔ Blue (cold) for temperature

- **📈 Time Series Charts**

  - Interactive line plots for selected variable(s)
  - X-axis: Days ahead (1–21)
  - Y-axis: Predicted value
  - Plotly zoom + hover for details

- **🎨 Variable Selector**

  - Tabs: Tmed, Tmin, Tmax, Rain, Sol, HR, Vel
  - Switch between variables without page reload (Streamlit reactivity)

- **📊 7-Day Summary Cards**

  - Quick overview: High/Low temp, Rain%, Wind speed, Sun hours
  - Emoji indicators: ☀️ (sunny), 🌧️ (rainy), ❄️ (cold), 🔥 (hot)

- **📥 Download Forecast**
  - CSV export of entire 21-day forecast
  - Excel-compatible for further analysis

**Data Flow:**

```
Load rainbow_forecast_final.csv
          ↓
User selects station + variable
          ↓
Filter data for that station
          ↓
Render Folium map + Plotly line chart
          ↓
Display summary cards
```

---

### ❄️ Persona 4: Health / Safety Officer

**Goal:** _"How cold/hot does it feel?"_

### Page 4: 🌡️ Wind Chill & Apparent Temperature

**URL:** `localhost:8501/04_Wind_Chill_Notify_Form` → Navigate to **Wind Chill**

**Purpose:** Calculate and alert on dangerous apparent temperatures

**Features:**

- **🔢 Interactive Calculator**

  - Input fields: Temperature (°C), Humidity (%), Wind speed (m/s)
  - Real-time calculation of:
    - **Wind Chill** (T < 10°C)
    - **Heat Index** (T > 25°C)
    - **Steadman Formula** (10°C ≤ T ≤ 25°C)

- **⚠️ Health Warnings**

  ```
  Wind Chill < -30°C:  🔴 SEVERE FROSTBITE RISK
  Wind Chill < -10°C:  🟠 FROSTBITE WARNING
  Wind Chill > 0°C:    🟡 COOL (caution advised)

  Heat Index > 41°C:   🔴 EXTREME HEAT (heat stroke)
  Heat Index > 32°C:   🟠 HEAT WARNING (caution)
  ```

- **📧 Notification Setup (Telegram Integration)**

  - Enable notifications for extreme conditions
  - Select stations to monitor
  - Set thresholds (e.g., alert if Wind Chill < -20°C)
  - **Integration:** `04_Wind_Chill_Notify_Form.py` sends alerts to Telegram

- **📊 Historical Extremes**
  - Table: Hottest/coldest days by apparent temperature (2025)
  - Useful for understanding local climate extremes

**Data Flow:**

```
User inputs: Temp, Humidity, Wind
          ↓
Calculate 3 apparent temperatures
          ↓
Display selected formula + health warning
          ↓
Optional: Enable Telegram notifications
          ↓
Alerts sent to user when thresholds exceeded
```

---

## 🧩 Reusable Components

All pages use shared components from `app/components/`:

### charts.py – Plotly Visualizations

```python
# Scatter plot (actual vs. predicted)
render_scatter(actual, predicted, title="Temperature Validation")

# Line chart (time series)
render_timeseries(dates, values, variable_name="Tmed")

# Box plot (distribution by season)
render_boxplot(data, groups=["Winter", "Spring", "Summer", "Fall"])
```

### maps.py – Folium Geospatial Maps

```python
# Create base map
m = folium.Map(center=(42.0, 2.0), zoom_start=8)

# Add station markers
for station in stations:
    folium.CircleMarker(
        location=[station.lat, station.lon],
        color=get_color(value),  # Color by value
        radius=5
    ).add_to(m)
```

### visuals.py – Custom Styling

```python
# Rainbow gauge (0–100%)
render_gauge(value=75, title="Rainbow Probability")

# Status badge (good/warning/danger)
render_status_badge(metric=0.72, thresholds=[0.6, 0.8])

# Color scale legend
render_legend(vmin=-10, vmax=30, label="°C")
```

### loading.py – Data Caching

```python
@st.cache_data
def load_forecast():
    """Cache forecast data (reuse across page loads)"""
    return pd.read_csv('data/predictions/rainbow_forecast_final.csv')

@st.cache_resource
def load_models():
    """Cache trained models (expensive operation)"""
    return joblib.load('models/lgbm_rain.pkl')
```

---

## 🔌 Data Integration

### Forecast Data (`data/predictions/rainbow_forecast_final.csv`)

```
Station,Date,Tmed,Tmin,Tmax,Sol,HRMedia,VelMedia,RainProb,RainbowProb,WindChill,HeatIndex
0061X,2025-01-15,8.5,3.2,14.1,2.3,65,2.1,0.45,0.12,-5.2,—
0061X,2025-01-16,9.2,4.1,15.3,4.5,58,1.8,0.22,0.08,-3.1,—
...
```

### Metadata (`data/raw/Station_Metadata.json`)

```json
{
  "stations": [
    {
      "id": "0061X",
      "name": "Pontons",
      "lat": 41.7234,
      "lon": 2.4156,
      "altitude": 320
    },
    ...
  ]
}
```

---

## 🎨 UI/UX Features

### Responsiveness

- Mobile-friendly layout (Streamlit handles responsivity automatically)
- Sidebar collapses on small screens
- Touch-friendly buttons and controls

### Performance

- `@st.cache_data` on forecast data (~100 ms load)
- `@st.cache_resource` on models (~10 ms load)
- Lazy rendering of plots (rendered only when selected)

### Accessibility

- High-contrast color schemes
- Emoji indicators (☀️, 🌧️, ❄️, 🔥)
- Alt-text on images
- Keyboard navigation supported

---

## 🚀 Launching the Dashboard

```bash
# From project root
uv run streamlit run app/main.py

# Opens automatically in browser:
#   http://localhost:8501
```

**Development Mode:**

```bash
# With auto-reload on file changes
streamlit run app/main.py --logger.level=debug
```

---

## 📁 Code Organization

```
app/
├── main.py                      # Entry point, layout, sidebar
│
├── pages/
│   ├── 01_Rainbow_Hunter.py     # Rainbow probability detector
│   ├── 02_Model_Audit.py        # Performance metrics & validation
│   ├── 03_Weather_Forecast.py   # 21-day forecast maps & charts
│   └── 04_Wind_Chill_Notify_Form.py # Apparent temp calculator
│
├── components/
│   ├── charts.py                # Plotly functions
│   ├── maps.py                  # Folium functions
│   ├── visuals.py               # Styling & custom widgets
│   └── loading.py               # Caching utilities
│
└── assets/
    └── style.css                # Custom CSS (optional)
```

---

## 🔧 Extending the Dashboard

### Add a New Page

1. Create `app/pages/05_My_New_Page.py`
2. Streamlit auto-discovers pages (alphabetical order)
3. Use standard structure:

   ```python
   import streamlit as st
   from app.components import charts, maps

   st.title("📊 My New Page")

   # Load data
   forecast = st.cache_data(load_forecast)()

   # Render components
   charts.render_timeseries(forecast['date'], forecast['tmed'])
   ```

### Add a New Component

1. Create function in `app/components/visuals.py`
2. Import and use in pages:
   ```python
   from app.components.visuals import my_new_widget
   my_new_widget(data)
   ```

---

**App Status:** Production-Ready | **Last Updated:** January 2026 | **Framework:** Streamlit 1.28+
