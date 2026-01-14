# 🤝 Contributing Guide

Thank you for contributing to **Rainbow AI**! This guide explains how to set up your development environment and follow the contribution workflow.

---

## 🛠️ Development Setup

### Option 1: Using `uv` (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/Meteorological-Prediction-System.git
cd Meteorological-Prediction-System

# Install dependencies with uv
uv sync

# Activate virtual environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate
```

### Option 2: Using `pip` & Virtual Environment

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Linux/macOS
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Option 3: Using `conda`

```bash
conda create -n rainbow-ai python=3.10
conda activate rainbow-ai
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check Python version
python --version     # Should be 3.10+

# Run a test pipeline
uv run pipelines/01_ingest_data.py --help
```

---

## 🔑 Configuration

### Environment Variables

Create a `.env` file in the project root with your API keys:

```bash
# .env
AEMET_API_KEY=your_aemet_api_key_here
```

**⚠️ IMPORTANT:** Never commit `.env` files to version control. Use `.env.example` as a template.

### Configuration File

All system settings are centralized in **`src/config/settings.py`**:

```python
# src/config/settings.py
class ModelConfig:
    RAIN_THRESHOLD = 0.3
    FORECAST_DAYS = 21
    LAG_DAYS = [1, 2, 7]
    ROLLING_WINDOWS = [3, 7, 14]
```

Modify this file to adjust model hyperparameters, data paths, or API endpoints.

---

## 📦 Running Pipelines Locally

### Full Data Pipeline (One-Time Setup)

```bash
# 1. Ingest historical AEMET data (4–6 hours)
uv run pipelines/01_ingest_data.py

# 2. Process and clean data (~30 minutes)
uv run pipelines/02_process_data.py

# 3. Train models and generate forecast (~10 minutes)
uv run pipelines/03_train_model.py
```

### Validation & Analysis (Optional)

```bash
# One-step forecast (teacher forcing)
uv run pipelines/04_onestep_forecast.py

# Recursive forecast (21-day error accumulation)
uv run pipelines/05_recursive_forecast.py

# Comparative metrics report
uv run pipelines/06_comparative_report.py

# Model explainability & feature importance
uv run pipelines/07_model_analysis.py
```

### Launch Dashboard

```bash
uv run streamlit run app/main.py
```

Opens at `http://localhost:8501`

---

## ✅ Code Style & Quality

### Python Code Style

Follow **PEP 8** with these conventions:

```python
# ✅ Good: Type hints, clear naming, docstrings
def calculate_wind_chill(
    temp_celsius: float,
    wind_speed_ms: float
) -> float:
    """Calculate Wind Chill Index using standard formula.

    Args:
        temp_celsius: Temperature in Celsius
        wind_speed_ms: Wind speed in meters per second

    Returns:
        Apparent temperature in Celsius
    """
    return 13.12 + 0.6215 * temp_celsius - ...
```

### Linting & Formatting

```bash
# Format code with Black
black src/ pipelines/ app/

# Lint with Ruff
ruff check src/ pipelines/ app/

# Type checking with mypy
mypy src/ --strict

# All checks together
uv run pre-commit run --all-files
```

### Docstrings

Use **Google style** docstrings:

```python
def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    model_name: str
) -> dict:
    """Train a LightGBM model with cross-validation.

    Args:
        X_train: Training features
        y_train: Training targets
        model_name: Identifier for saved model

    Returns:
        Dictionary containing:
            - 'model': Trained LightGBM booster
            - 'cv_scores': Cross-validation metrics
            - 'feature_importance': Feature ranking

    Raises:
        ValueError: If X_train and y_train have mismatched lengths
    """
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/etl/test_processing.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run tests in verbose mode
pytest -vv
```

### Writing Tests

Place tests in `tests/` mirroring the `src/` structure:

```
tests/
├── etl/
│   ├── __init__.py
│   └── test_processing.py
├── features/
│   └── test_transformation.py
├── modeling/
│   └── test_base.py
└── schemas/
    └── test_weather.py
```

**Example test:**

```python
# tests/features/test_transformation.py
import pytest
import pandas as pd
from src.features.transformation import create_lag_features

def test_create_lag_features():
    """Test lag feature creation with known data."""
    # Arrange
    data = pd.DataFrame({'value': [1, 2, 3, 4, 5]})

    # Act
    result = create_lag_features(data, lag_days=[1, 2])

    # Assert
    assert 'value_lag_1' in result.columns
    assert 'value_lag_2' in result.columns
    assert pd.isna(result['value_lag_1'].iloc[0])  # First row is NaN
```

---

## 🚀 Adding a New Feature or Model

### Step 1: Create Code in `src/`

```python
# src/modeling/trainers/new_model.py
from src.modeling.base import BaseModel

class NewWeatherModel(BaseModel):
    """Custom model for a new weather variable."""

    def __init__(self, model_name: str):
        super().__init__(model_name)

    def preprocess(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply custom preprocessing."""
        # Your preprocessing logic
        return X
```

### Step 2: Add Unit Tests

```python
# tests/modeling/test_new_model.py
import pytest
from src.modeling.trainers.new_model import NewWeatherModel

def test_new_model_initialization():
    """Test model instantiation."""
    model = NewWeatherModel('test_model')
    assert model.name == 'test_model'
```

### Step 3: Integrate into Pipeline

```python
# pipelines/03_train_model.py
from src.modeling.trainers.new_model import NewWeatherModel

# Add to main orchestration
new_model = NewWeatherModel('new_var')
new_model.fit(X_train, y_train)
new_model.save('models/new_var.pkl')
```

### Step 4: Update Documentation

- Update [logic.md](logic.md) with feature/model description
- Update [pipelines.md](pipelines.md) if pipeline order changed
- Update [architecture.md](architecture.md) if folder structure changed

### Step 5: Submit Pull Request

```bash
# Create feature branch
git checkout -b feature/my-new-model

# Commit changes
git add src/ tests/ docs/ pipelines/
git commit -m "Add new weather model for [variable name]"

# Push and create PR
git push origin feature/my-new-model
```

---

## 📋 Git Workflow

### Branch Naming Conventions

```
feature/add-new-model          # New feature
bugfix/fix-data-leak           # Bug fix
docs/update-architecture       # Documentation
refactor/simplify-etl-code     # Code refactoring
```

### Commit Message Format

```
[TYPE] Brief description

Optional longer explanation:
- What was changed
- Why it was changed
- Any side effects or notes

Examples:
✅ [FEATURE] Add LSTM model for solar radiation prediction
✅ [BUGFIX] Fix missing value imputation in humidity
✅ [DOCS] Update results.md with 2025 metrics
```

### Pull Request Checklist

- [ ] Tests pass locally (`pytest`)
- [ ] Code follows style guide (`black`, `ruff`)
- [ ] Documentation updated
- [ ] No hardcoded API keys or secrets
- [ ] Commit messages are clear
- [ ] No unrelated changes included

---

## 🔐 Security Best Practices

### API Keys & Secrets

```bash
# ✅ CORRECT: Store in .env (never commit)
AEMET_API_KEY=sk_live_abc123

# ❌ WRONG: Hardcode in Python
api_key = "sk_live_abc123"  # Exposed!
```

### Data Management

- Large files (`data/raw/`, `models/`) are **gitignored**
- Use cloud storage (S3, GCS) for production artifacts
- Never commit `.pkl` or `.joblib` files to Git

### Dependency Security

```bash
# Check for vulnerable dependencies
pip list --outdated
pip install --upgrade pip setuptools

# Use dependency pinning in production
pip freeze > requirements.txt
```

---

## 📚 Project Structure Reference

```
Meteorological-Prediction-System/
│
├── src/                        # Core domain logic
│   ├── config/settings.py      # Configuration (edit for hyperparameters)
│   ├── etl/                    # Data ingestion & processing
│   ├── features/               # Feature engineering
│   ├── modeling/               # ML models & heuristics
│   ├── schemas/                # Data validation
│   └── utils/                  # Shared utilities
│
├── pipelines/                  # Orchestration scripts (01–07)
├── app/                        # Streamlit frontend
├── tests/                      # Unit & integration tests
├── docs/                       # Documentation (markdown)
├── data/                       # Data storage (raw, processed, predictions)
├── models/                     # Trained model artifacts
│
├── pyproject.toml              # Project metadata & dependencies
├── pytest.ini                  # Pytest configuration
├── .gitignore                  # Git ignore rules
├── .env.example                # Template for environment variables
├── LICENSE                     # MIT License
└── README.md                   # Quick start guide
```

---

## 🆘 Getting Help

- **Documentation:** Check the docs folder for architecture, pipelines, and logic
- **Issues:** Search existing issues or create a new one
- **Discussions:** Use GitHub Discussions for questions
- **Code Review:** Tag maintainers on pull requests

---

## 📝 License

By contributing, you agree that your contributions are licensed under the **MIT License** (see project root for LICENSE file).

---

**Last Updated:** January 2026 | **Status:** Accepting Contributions
