"""
Rain Classification Model.
Predicts binary precipitation probability.
"""

import joblib
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

from src.config.settings import Paths
from src.features.transformation import FeatureEngineer
from src.modeling.base import BaseModel
from src.utils.logger import log


class RainClassifier(BaseModel):
    def run_training(self):
        self.load_and_prepare()
        df_eng = self.df.copy()

        # Threshold for "Is Raining" (mm)
        THRESHOLD = 0.1

        # ---------------------------------------------------------
        # 1. PHYSICS FEATURES
        # ---------------------------------------------------------
        # Pressure Tendency (The Storm Engine)
        if "presion" in df_eng.columns:
            df_eng["presion_diff"] = df_eng.groupby("indicativo")["presion"].diff()

        # Cloud Physics
        if "nubes" in df_eng.columns and "hrMedia" in df_eng.columns:
            df_eng["cloud_moisture"] = df_eng["nubes"] * df_eng["hrMedia"]

        # ---------------------------------------------------------
        # 2. TEMPORAL FEATURES
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
        df_eng = FeatureEngineer.create_lags(df_eng, lag_cols, [1, 2, 3])

        # Rolling Pressure (Short term trend)
        df_eng = FeatureEngineer.create_rolling_stats(df_eng, ["presion"], [3])

        # ---------------------------------------------------------
        # 3. TARGET CREATION
        # ---------------------------------------------------------
        df_eng = df_eng.dropna()
        # Target: Will it rain tomorrow?
        df_eng["target_rain"] = (
            df_eng.groupby("indicativo")["prec"].shift(-1) > THRESHOLD
        ).astype(int)

        df_eng = df_eng.dropna(subset=["target_rain"])

        # ---------------------------------------------------------
        # 4. TRAINING (CLASSIFICATION OVERRIDE)
        # ---------------------------------------------------------
        cutoff = "2023-01-01"
        train = df_eng[df_eng["fecha"] < cutoff]
        test = df_eng[df_eng["fecha"] >= cutoff]

        drop_cols = ["fecha", "indicativo", "nombre", "provincia", "target_rain"]
        X_train = train.drop(columns=drop_cols, errors="ignore")
        y_train = train["target_rain"]
        X_test = test.drop(columns=drop_cols, errors="ignore")
        y_test = test["target_rain"]

        log.info(f"☔ Training Rain Classifier ({X_train.shape[1]} features)...")

        train_ds = lgb.Dataset(X_train, label=y_train)
        test_ds = lgb.Dataset(X_test, label=y_test, reference=train_ds)

        params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "num_leaves": 40,
            "learning_rate": 0.04,
            "feature_fraction": 0.8,
            "verbose": -1,
        }

        model = lgb.train(
            params,
            train_ds,
            num_boost_round=1500,
            valid_sets=[train_ds, test_ds],
            callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)],
        )

        # Save
        path = Paths.MODELS / "lgbm_rain_classifier.pkl"
        path.parent.mkdir(exist_ok=True)
        joblib.dump(model, path)

        # ---------------------------------------------------------
        # 5. PREDICTION
        # ---------------------------------------------------------
        probs = model.predict(X_test)
        auc = roc_auc_score(y_test, probs)

        log.info(f"   📊 Mean Prob: {probs.mean():.2f}")
        log.info(f"   🏆 ROC-AUC: {auc:.4f}")

        results = test[["fecha", "indicativo"]].copy()
        results["prob_rain"] = probs
        results["is_raining"] = (probs > 0.5).astype(int)

        return results
