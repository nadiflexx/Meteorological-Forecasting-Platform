import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_scatter_vs_real(
    df: pd.DataFrame, target: str, title: str, unit: str
) -> px.scatter:
    """
    Generates a professional scatter plot comparing predicted vs real values.

    Args:
        df: Dataframe containing validation data.
        target: The target variable code (e.g., 'tmed', 'velmedia').
        title: Chart title.
        unit: Unit of measurement (e.g., '°C').
    """
    real_col = f"real_{target}"
    pred_col = f"pred_{target}"

    # Check if cols exist
    if real_col not in df.columns or pred_col not in df.columns:
        return go.Figure()

    # Sample for performance
    df_plot = df.sample(n=min(2000, len(df)), random_state=42)

    min_val = min(df_plot[real_col].min(), df_plot[pred_col].min())
    max_val = max(df_plot[real_col].max(), df_plot[pred_col].max())

    fig = px.scatter(
        df_plot,
        x=real_col,
        y=pred_col,
        color=real_col,
        color_continuous_scale="Viridis",
        title=f"{title} (Predicted vs Real)",
        labels={real_col: f"Real {unit}", pred_col: f"Predicted {unit}"},
        opacity=0.6,
    )

    # Add perfect prediction line (y=x)
    fig.add_shape(
        type="line",
        x0=min_val,
        y0=min_val,
        x1=max_val,
        y1=max_val,
        line={"color": "Red", "width": 2, "dash": "dash"},
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        xaxis={"showgrid": True, "gridcolor": "#F1F5F9"},
        yaxis={"showgrid": True, "gridcolor": "#F1F5F9"},
    )

    return fig


def plot_confusion_matrix(tn, fp, fn, tp):
    """
    Generates a Confusion Matrix where:
    - Diagonal (TN, TP) is GREEN (Good).
    - Off-Diagonal (FP, FN) is RED (Bad).
    """
    z_color = [[1, 0], [0, 1]]
    z_text = [[str(tn), str(fp)], [str(fn), str(tp)]]

    x = ["Predicted: NO", "Predicted: YES"]
    y = ["Actual: NO", "Actual: YES"]

    fig = px.imshow(
        z_color,
        x=x,
        y=y,
        color_continuous_scale=[
            [0, "#EF4444"],
            [1, "#22C55E"],
        ],
        zmin=0,
        zmax=1,
        aspect="auto",
    )
    total = tn + fp + fn + tp

    annotations = []
    for i in range(2):
        for j in range(2):
            count = int(z_text[i][j])
            perc = count / total * 100

            if i == 0 and j == 0:
                label = "TN (Correct Dry)"
            elif i == 0 and j == 1:
                label = "FP (False Alarm)"
            elif i == 1 and j == 0:
                label = "FN (Missed Rain)"
            elif i == 1 and j == 1:
                label = "TP (Correct Rain)"

            annotations.append(
                {
                    "x": x[j],
                    "y": y[i],
                    "text": f"<b>{count}</b><br>({perc:.1f}%)<br><span style='font-size:10px'>{label}</span>",
                    "showarrow": False,
                    "font": {"size": 16, "color": "white"},
                }
            )

    fig.update_layout(
        title="Confusion Matrix (Traffic Light Logic)",
        coloraxis_showscale=False,
        annotations=annotations,
    )

    return fig


def plot_rain_probability_hist(df):
    """Shows how the model separates rain vs dry days."""
    df_plot = df.copy()
    df_plot["Condition"] = np.where(df_plot["real_prec"] > 0.1, "Rainy Day", "Dry Day")

    fig = px.histogram(
        df_plot,
        x="pred_prob_rain",
        color="Condition",
        marginal="box",
        barmode="overlay",
        title="Probability Distribution by Real Condition",
        labels={"pred_prob_rain": "Predicted Probability"},
        color_discrete_map={"Rainy Day": "#3B82F6", "Dry Day": "#94A3B8"},
    )
    return fig


def plot_weekly_temperature_trend(df_week: pd.DataFrame) -> go.Figure:
    """
    Generates a line chart showing Min, Max, and Avg temperatures over a week.

    Args:
        df_week (pd.DataFrame): Dataframe containing 'fecha_dt', 'pred_tmax', 'pred_tmin', 'pred_tmed'.

    Returns:
        go.Figure: Plotly figure.
    """
    fig = go.Figure()

    # 1. Max Temp Line
    fig.add_trace(
        go.Scatter(
            x=df_week["fecha_dt"],
            y=df_week["pred_tmax"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # 2. Min Temp Line
    fig.add_trace(
        go.Scatter(
            x=df_week["fecha_dt"],
            y=df_week["pred_tmin"],
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(255, 165, 0, 0.15)",
            name="Temp Range",
            hoverinfo="skip",
        )
    )

    # 3. Average Temp Line
    fig.add_trace(
        go.Scatter(
            x=df_week["fecha_dt"],
            y=df_week["pred_tmed"],
            mode="lines+markers",
            line={"color": "#F59E0B", "width": 3},
            marker={
                "size": 8,
                "color": "white",
                "line": {"width": 2, "color": "#F59E0B"},
            },
            name="Avg Temp",
        )
    )

    # 4. Rain Bars (Visual context)
    fig.add_trace(
        go.Bar(
            x=df_week["fecha_dt"],
            y=df_week["prob_rain"] * 5,
            name="Rain Prob (Scaled)",
            marker_color="#3B82F6",
            opacity=0.3,
            hoverinfo="skip",
        )
    )

    # 4. Wind Chill Line (NUEVA)
    fig.add_trace(
        go.Scatter(
            x=df_week["fecha_dt"],
            y=df_week["pred_windchill"],
            mode="lines+markers",
            line={"color": "#8B5CF6", "width": 2, "dash": "dot"},
            marker={"size": 6, "color": "#8B5CF6", "symbol": "diamond"},
            name="Wind Chill",
            hovertemplate="<b>AVG Wind Chill</b><br>%{y:.1f}°C<extra></extra>",
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin={"t": 20, "b": 20, "l": 40, "r": 20},
        xaxis={
            "showgrid": False,
            "tickformat": "%a %d",
        },
        yaxis={
            "showgrid": True,
            "gridcolor": "#F1F5F9",
            "title": "Temperature (°C)",
            "zeroline": False,
        },
        showlegend=False,
        hovermode="x unified",
    )

    return fig
