"""
Rain Classification Model.

Specialized trainer for predicting binary precipitation probability.
It overrides the standard regression approach to focus on classifying
days as "Wet" or "Dry" based on a specific physical threshold.
"""

import joblib
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

from src.config.settings import Paths
from src.features.transformation import FeatureEngineer
from src.modeling.base import BaseModel
from src.utils.logger import log


class RainClassifier(BaseModel):
    """
    Binary Classifier for Precipitation.

    Instead of predicting the exact amount of rain (mm) —which is notoriously
    difficult due to the zero-inflated distribution— this model predicts the
    **Probability of Rain** occurring (> 0.1mm).

    Key Logic:
    - Uses Barometric Pressure Tendency (t - t-1) as a primary predictor for fronts.
    - Optimizes for ROC-AUC (Area Under the Curve) rather than Error (MAE).
    """

    def run_training(self):
        """
        Executes the training pipeline for Rain Prediction.

        Workflow:
        1.  **Physics Features**: Calculates pressure differentials and cloud-moisture interactions.
        2.  **Temporal Features**: Generates lags to capture the approach of weather fronts.
        3.  **Target Definition**: Shifts data to predict t+1. Converts continuous rain (mm)
            to binary (0/1) using a threshold of 0.1mm.
        4.  **Data Splitting**: Uses Train (2009-2020), Val (2021-2022), Test (2023-2025).
        5.  **Training**: Specific LightGBM configuration for binary classification.

        Returns:
            pd.DataFrame: DataFrame containing 'prob_rain' (0.0-1.0) and 'is_raining' (0/1).
        """
        self.load_and_prepare()
        df_eng = self.df.copy()

        # Threshold to define "Is Raining"
        THRESHOLD = 0.1

        # ---------------------------------------------------------
        # 1. PHYSICS-BASED FEATURE ENGINEERING
        # ---------------------------------------------------------
        # Barometric Tendency: A rapid drop in pressure usually signals a storm.
        if "presion" in df_eng.columns:
            df_eng["presion_diff"] = df_eng.groupby("indicativo")["presion"].diff()

        # Cloud-Moisture Interaction:
        # High clouds + High humidity = Higher chance of rain than High clouds + Dry air.
        if "nubes" in df_eng.columns and "hrMedia" in df_eng.columns:
            df_eng["cloud_moisture"] = df_eng["nubes"] * df_eng["hrMedia"]

        # ---------------------------------------------------------
        # 2. TEMPORAL FEATURES (Time Series Context)
        # ---------------------------------------------------------
        lag_cols = [
            "prec",
            "presion",
            "presion_diff",
            "hrMedia",
            "nubes",
            "velmedia",
            "sol",
            "tmin",
            "cloud_moisture",
        ]
        # Create Lags (Previous days context)
        df_eng = FeatureEngineer.create_lags(df_eng, lag_cols, [1, 2, 3])

        # Rolling Pressure (Short term trend over 3 days)
        df_eng = FeatureEngineer.create_rolling_stats(df_eng, ["presion"], [3])

        # ---------------------------------------------------------
        # 3. TARGET CREATION
        # ---------------------------------------------------------
        df_eng = df_eng.dropna()

        # Target: Will it rain TOMORROW? (Shift -1)
        # We convert the boolean result to integer (1 = Yes, 0 = No)
        df_eng["target_rain"] = (
            df_eng.groupby("indicativo")["prec"].shift(-1) > THRESHOLD
        ).astype(int)

        # Drop the last row of each group which has no target
        df_eng = df_eng.dropna(subset=["target_rain"])

        # ---------------------------------------------------------
        # 4. TRAINING (CLASSIFICATION CONFIGURATION)
        # ---------------------------------------------------------
        # We override the generic train_lgbm method here because we need
        # 'binary' objective and 'auc' metric, not 'regression'/'mae'.

        # --- 3-WAY SPLIT LOGIC ---
        VAL_START = "2021-01-01"
        TEST_START = "2023-01-01"

        train = df_eng[df_eng["fecha"] < VAL_START]
        val = df_eng[(df_eng["fecha"] >= VAL_START) & (df_eng["fecha"] < TEST_START)]
        test = df_eng[df_eng["fecha"] >= TEST_START]

        drop_cols = ["fecha", "indicativo", "nombre", "provincia", "target_rain"]

        # Prepare Feature Matrices (X) and Target Vectors (y)
        X_train = train.drop(columns=drop_cols, errors="ignore")
        y_train = train["target_rain"]

        X_val = val.drop(columns=drop_cols, errors="ignore")
        y_val = val["target_rain"]

        X_test = test.drop(columns=drop_cols, errors="ignore")
        y_test = test["target_rain"]

        log.info(f"☔ Training Rain Classifier ({X_train.shape[1]} features)...")

        # Create LightGBM Datasets
        train_ds = lgb.Dataset(X_train, label=y_train)
        # Use validation set for reference to ensure binning consistency
        val_ds = lgb.Dataset(X_val, label=y_val, reference=train_ds)

        params = {
            "objective": "binary",
            "metric": "auc",  # Area Under Curve is best for imbalanced binary tasks
            "boosting_type": "gbdt",
            "num_leaves": 40,
            "learning_rate": 0.04,
            "feature_fraction": 0.8,
            "verbose": -1,
        }

        # Train with Early Stopping monitoring VALIDATION set
        model = lgb.train(
            params,
            train_ds,
            num_boost_round=1500,
            valid_sets=[train_ds, val_ds],
            callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)],
        )

        # Persistence
        path = Paths.MODELS / "lgbm_rain_classifier.pkl"
        path.parent.mkdir(exist_ok=True)
        joblib.dump(model, path)

        # ---------------------------------------------------------
        # 5. PREDICTION & EVALUATION (ON TEST SET)
        # ---------------------------------------------------------
        # We predict on X_test (which was NOT used for training or stopping)
        probs = model.predict(X_test)
        auc = roc_auc_score(y_test, probs)

        log.info(f"   📊 Mean Prob: {probs.mean():.2f}")
        log.info(f"   🏆 TEST SET ROC-AUC: {auc:.4f}")

        results = test[["fecha", "indicativo"]].copy()
        results["prob_rain"] = probs
        # We store the binary decision (using 0.5 as cutoff) for the UI
        results["is_raining"] = (probs > 0.5).astype(int)

        return results
