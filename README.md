# Meteorological-Prediction-System

Este proyecto tiene como objetivo principal proporcionar un simulador de predicción meteorológica preciso y eficiente, aprovechando las capacidades de Big Data para gestionar grandes volúmenes de datos y realizar previsiones a corto plazo con alta precisión.

# P3 Predicción Meteorológica con IA

Proyecto de predicción meteorológica en Python usando modelos de aprendizaje automático (Random Forest).

## Estructura del proyecto

```
P3_Prediccion_Meteorologica_IA/
├── src/
│   ├── train_model.py        # Entrena modelos con datos 2020–2024
│   └── predict_future.py     # Genera predicciones para 2025
├── data/processed/           # Resultados (CSV para Power BI)
├── models/                   # Modelos entrenados (.pkl)
└── README.md
```

## Cómo usarlo

1️⃣ Instalar dependencias (usando `uv` o `pip`):

```bash
uv venv
uv pip install pandas numpy scikit-learn joblib
```

2️⃣ Entrenar modelos (usa datos simulados 2020–2024):

```bash
uv run python src/train_model.py
```

3️⃣ Generar predicciones para 2025:

```bash
uv run python src/predict_future.py
```

4️⃣ El resultado se guarda en:

```
data/processed/predicciones_2025.csv
```

Ese archivo puede cargarse en Power BI para visualizar la predicción diaria de temperatura, precipitación y probabilidad de lluvia para 2025.
