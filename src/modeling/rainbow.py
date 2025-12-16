import numpy as np


class RainbowCalculator:
    def calculate_probability(self, df_preds):
        df = df_preds.copy()

        # ---------------------------------------------------------
        # 1. FACTOR LLUVIA (Probabilidad de precipitación)
        # ---------------------------------------------------------
        # Buscamos que llueva, pero si la probabilidad es 99%,
        # suele implicar cielo cubierto gris (Stratocumulus), lo que mata el arcoíris.
        conditions_rain = [
            (df["prob_rain"] < 0.25),  # Muy seco -> 0% chance
            (df["prob_rain"] >= 0.25)
            & (df["prob_rain"] <= 0.85),  # IDEAL: Chubascos dispersos
            (df["prob_rain"] > 0.85),  # Lluvia muy generalizada (Cielo gris)
        ]
        values_rain = [
            0.0,
            1.0,
            0.7,
        ]  # Bajamos un poco el score si es lluvia muy segura

        df["score_rain"] = np.select(conditions_rain, values_rain)

        # Matiz: Multiplicamos por la propia probabilidad para diferenciar un 30% de un 80%
        df["score_rain"] = df["score_rain"] * df["prob_rain"]

        # ---------------------------------------------------------
        # 2. FACTOR SOL (Horas de insolación) - ACTUALIZADO
        # ---------------------------------------------------------
        # Ahora que tienes datos reales (0 a 15 horas):
        # - < 1h: Oscuro/Gris total.
        # - 1h - 4h: Mayormente nublado, pero con algún claro (Posible).
        # - 4h - 10h: IDEAL. "Nubes y Claros". Clima dinámico.
        # - > 10h: Mayormente despejado. Difícil que coincida con lluvia, pero si pasa, es arcoíris seguro.

        conditions_sol = [
            (df["pred_sol"] < 1.0),  # Demasiado nublado (Gris)
            (df["pred_sol"] >= 1.0) & (df["pred_sol"] < 4.0),  # Nublado con roturas
            (df["pred_sol"] >= 4.0) & (df["pred_sol"] < 10.0),  # IDEAL (Clima variable)
            (df["pred_sol"] >= 10.0),  # Muy soleado
        ]
        # Puntuaciones
        values_sol = [0.0, 0.6, 1.0, 0.8]

        df["score_sol"] = np.select(conditions_sol, values_sol)

        # ---------------------------------------------------------
        # 3. FACTOR HUMEDAD (Humedad Relativa Media)
        # ---------------------------------------------------------
        # Los arcoíris aman la humedad alta pero con visibilidad.
        # hrMedia baja (<40%) evapora las gotas rápido.
        df["factor_humedad"] = df["pred_hrMedia"] / 100.0

        # Penalizamos si es muy baja
        df.loc[df["pred_hrMedia"] < 40, "factor_humedad"] *= 0.5

        # ---------------------------------------------------------
        # FÓRMULA FINAL
        # ---------------------------------------------------------
        # Probabilidad = (Lluvia * Sol * Humedad)
        # Multiplicamos por 100 y ajustamos un factor de escala (x1.2) para ser optimistas
        # ya que la coincidencia exacta es rara.
        raw_prob = (df["score_rain"] * df["score_sol"] * df["factor_humedad"]) * 120

        df["rainbow_prob"] = raw_prob.clip(0, 95).round(1)

        return df[
            [
                "fecha",
                "indicativo",
                "rainbow_prob",
                "prob_rain",
                "is_raining",
                "pred_sol",
                "pred_hrMedia",  # Útil para debug
            ]
        ]
