# 🏗️ System Architecture

The project adopts a **Modular Layered Architecture**, enabling separation of concerns between Data Engineering, Machine Learning logic, and User Interface. This structure facilitates testing, scalability, and maintenance.

## 🌳 Full Directory Structure

```text
METEOROLOGICAL-PREDICTION-SYSTEM/
│
├── 📂 app/                          # FRONTEND (Presentation Layer)
│   ├── 📂 assets/
│   │   └── style.css                # Global styling (Fonts, Shadows, Colors)
│   ├── 📂 components/               # UI Widgets (Isolated Logic)
│   │   ├── charts.py                # Plotly configurations
│   │   ├── loading.py               # Startup animation logic
│   │   ├── maps.py                  # Folium geospatial rendering
│   │   └── visuals.py               # SVG Rainbow rendering
│   ├── 📂 pages/                    # Streamlit Views
│   │   ├── 01_Rainbow_Hunter.py     # Main Dashboard
│   │   ├── 02_Model_Audit.py        # Technical Evaluation
│   │   └── 03_Weather_Forecast.py   # General Weather Sim
│   ├── 📂 utils/
│   │   └── data_loader.py           # Frontend Caching & Data IO
│   └── main.py                      # Application Entry Point
│
├── 📂 pipelines/                    # ORCHESTRATION LAYER (Execution)
│   ├── 01_ingest_data.py            # Trigger AEMET ETL
│   ├── 02_process_data.py           # Trigger Cleaning & Enrichment
│   └── 03_train_model.py            # Trigger ML Training
│
├── 📂 src/                          # BACKEND CORE (Domain Logic)
│   ├── 📂 config/
│   │   └── settings.py              # Single Source of Truth (Paths, APIs)
│   ├── 📂 etl/                      # Extract-Transform-Load
│   │   ├── 📂 clients/
│   │   │   ├── aemet.py             # AEMET API Wrapper
│   │   │   └── openmeteo.py         # Open-Meteo API Wrapper
│   │   ├── ingestion.py             # File System & atomic writes
│   │   └── processing.py            # Data fusion & Imputation logic
│   ├── 📂 features/                 # FEATURE ENGINEERING
│   │   ├── physics.py               # Thermodynamic formulas (Magnus, VPD)
│   │   └── transformation.py        # Maths (Lags, Rolling, Cyclical)
│   ├── 📂 modeling/                 # MACHINE LEARNING
│   │   ├── 📂 trainers/             # Specific Model Configurations
│   │   │   ├── atmosphere.py        # Solar/Wind/Humidity models
│   │   │   ├── rain.py              # Rain Classifier
│   │   │   └── temperature.py       # Temp Regressors
│   │   ├── base.py                  # LightGBM Wrapper (Train/Save/Load)
│   │   └── rainbow.py               # Rainbow Heuristic Logic
│   ├── 📂 schemas/                  # DATA VALIDATION
│   │   └── weather.py               # Pydantic Schemas
│   └── 📂 utils/                    # SHARED UTILITIES
│       ├── cleaner.py               # Cleanup scripts
│       ├── logger.py                # Centralized Logging system
│       └── resilience.py            # Handles API Calls with Exponential Backoff
└── 📂 docs/                         # DOCUMENTATION (MkDocs)
```

## 🔍 Module Breakdown

### 1. Presentation Layer (`app/`)

- **`main.py`**: The **Entry Point**. It orchestrates the app startup:
  1.  Sets page configuration.
  2.  Runs the Loading Screen animation.
  3.  Injects CSS styles.
  4.  Renders the Landing Page.
- **`assets/style.css`**: Defines the "Rainbow Theme". It overrides standard Streamlit components to give a polished, custom look (rounded cards, purple accents, custom fonts).
- **`utils/data_loader.py`**: Uses `st.cache_data` to load heavy CSV files into RAM once. It also pre-converts date columns to `datetime` objects to optimize performance across pages.

### 2. Execution Layer (`pipelines/`)

- **`01_ingest_data.py`**:
  - Reads station list from `settings.py`.
  - Calls `src.etl.clients.aemet` to fetch data in 6-month chunks.
  - Handles retries and consolidates data into yearly JSON files.
- **`02_process_data.py`**:
  - Loads raw JSONs.
  - Calls `src.etl.clients.openmeteo` to fetch missing physical variables (Pressure, Clouds).
  - Executes the Merge logic (`Left Join` on Date).
  - Fills gaps using Linear Interpolation.
- **`03_train_model.py`**:
  - Generates features (Lags, Rolling).
  - Trains 7 LightGBM models.
  - Derives complex variables (Humidity from Temp/DewPoint).
  - Calculates Rainbow Probability.
  - Exports final results for the App.

### 3. Backend Core (`src/`)

#### `src/config/`

- **`settings.py`**: The **Single Source of Truth**. Instead of hardcoding paths or keys, everything is defined here. It uses a `Paths` class to dynamically resolve directory locations, making the code portable across different operating systems.

#### `src/etl/` (Data Engineering)

- **`clients/`**: Wrappers for external APIs.
  - `aemet.py`: Handles 429 Rate Limits with exponential backoff loops to ensure data completeness.
  - `openmeteo.py`: Maps variables and adjusts Timezones (+6h shift) to align UTC data with Local daily aggregates.
- **`ingestion.py`**: Handles File System logic. Uses `os.fsync()` to ensure data is physically written to disk before proceeding, preventing race conditions.
- **`processing.py`**: The core data pipeline logic. It acts as the "Controller" for cleaning, filtering bad stations (<85% data), and merging datasets.

#### `src/features/` (The "Brain")

Separates mathematical logic from training logic.

- **`physics.py`**: Contains static methods for thermodynamic calculations.
  - _Example:_ Calculating **Relative Humidity** derived from Temperature and Dew Point using the **Magnus-Tetens Formula**.
- **`transformation.py`**: Handles statistical feature generation.
  - _Example:_ `add_time_cyclicality` converts 1-12 (Months) into Sine/Cosine waves so the model understands seasonality (e.g., December is close to January).
  - _Example:_ creating Time Lags (t-1, t-2) and Rolling Windows.

#### `src/schemas/`

- **`weather.py`**: Uses **Pydantic** to enforce data integrity. It validates every single data point downloaded from AEMET. If a field is missing or wrong (e.g., text in a float field), it cleans it or flags it before it enters the system.

#### `src/modeling/` (Machine Learning)

- **`base.py`**: The parent class. It handles the standardized ML operations: loading data, splitting Train/Test, training LightGBM, and saving `.pkl` binary files.
- **`trainers/*.py`**: Specific implementations for each target variable.
  - `rain.py`: Defines the target as Binary (>0.1mm) and selects pressure-based features.
  - `atmosphere.py`: Defines targets as Regression (Solar, Wind, Humidity).
- **`rainbow.py`**: The business logic layer. It takes the raw ML predictions and applies the heuristic formula: $P = Rain \times Sun \times Humidity$.

#### `src/utils/`

- **`logger.py`**: Sets up a standardized Python Logger. It outputs colored logs to the console for real-time monitoring and detailed logs to `logs/execution.log` for historical debugging.
- **`resilience.py`**: Contains the `fetch_with_retry_logic` wrapper. It implements **Exponential Backoff** strategies to handle API timeouts and empty responses gracefully without crashing the pipeline.
