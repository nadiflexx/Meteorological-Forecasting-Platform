from src.modeling.base import BaseModel


class TemperatureModel(BaseModel):
    def run_training(self):
        """Entrena Tmed, Tmin, Tmax en bucle"""
        self.load_and_prepare()
        targets = ["tmed", "tmin", "tmax"]

        # Features
        cols_lag = ["tmed", "tmin", "tmax", "presMin"]
        lags = [1, 2, 7]

        df_eng = self.df.copy()
        for col in cols_lag:
            if col in df_eng.columns:
                for lag in lags:
                    df_eng[f"{col}_lag_{lag}"] = df_eng.groupby("indicativo")[
                        col
                    ].shift(lag)

        for w in [7, 14]:
            if "tmed" in df_eng.columns:
                df_eng[f"tmed_roll_{w}"] = df_eng.groupby("indicativo")[
                    "tmed"
                ].transform(lambda x, window=w: x.rolling(window).mean())

        df_eng = df_eng.dropna()

        cutoff = "2023-01-01"
        train = df_eng[df_eng["fecha"] < cutoff]
        test = df_eng[df_eng["fecha"] >= cutoff]

        results = test[["fecha", "indicativo"]].copy()

        for target in targets:
            if target not in df_eng.columns:
                continue

            # Target Shift (-1 para predecir mañana)
            y_train = train.groupby("indicativo")[target].shift(-1).dropna()
            y_test = test.groupby("indicativo")[target].shift(-1).dropna()

            # Alinear X con y
            X_train = train.loc[y_train.index].drop(
                columns=["fecha", "indicativo", "nombre", "provincia"]
            )
            X_test = test.loc[y_test.index].drop(
                columns=["fecha", "indicativo", "nombre", "provincia"]
            )

            # Entrenar
            preds = self.train_lgbm(X_train, y_train, X_test, y_test, target)

            # --- CORRECCIÓN AQUÍ ---
            # Asignamos usando el índice de y_test para alinear las filas exactas.
            # Las filas que sobran (el último día) se quedarán como NaN.
            results.loc[y_test.index, f"pred_{target}"] = preds

        # Eliminamos las filas que quedaron vacías (los últimos días de cada estación)
        results = results.dropna()

        return results
