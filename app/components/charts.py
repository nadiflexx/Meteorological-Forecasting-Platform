import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_rainbow_gauge(probability: float) -> go.Figure:
    """
    Generates a speedometer-style gauge chart for rainbow probability.

    Args:
        probability (float): The calculated probability (0-100).

    Returns:
        go.Figure: Plotly figure object.
    """
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability,
            number={"suffix": "%", "font": {"size": 40, "color": "#1E293B"}},
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": "Rainbow Probability",
                "font": {"size": 20, "color": "#64748B"},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "white"},
                "bar": {"color": "rgba(0,0,0,0)"},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "white",
                "steps": [
                    {"range": [0, 30], "color": "#F1F5F9"},  # Gray (Low)
                    {"range": [30, 60], "color": "#FEF08A"},  # Yellow (Medium)
                    {"range": [60, 100], "color": "#86EFAC"},  # Green (High)
                ],
                "threshold": {
                    "line": {"color": "#7C3AED", "width": 5},
                    "thickness": 0.75,
                    "value": probability,
                },
            },
        )
    )
    fig.update_layout(
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter"},
    )
    return fig


def plot_scatter_vs_real(df: pd.DataFrame, target_name: str) -> px.scatter:
    """
    Generates a professional scatter plot comparing predicted vs real values.

    Args:
        df (pd.DataFrame): Dataframe containing 'real_value' and 'predicted_value'.
        target_name (str): Name of the target variable for the title.

    Returns:
        px.scatter: Plotly figure object.
    """
    fig = px.scatter(
        df,
        x="real_value",
        y="predicted_value",
        opacity=0.4,
        trendline="ols",
        trendline_color_override="#EF4444",
        labels={
            "real_value": "Real Value (Observed)",
            "predicted_value": "AI Prediction",
        },
        color_discrete_sequence=["#7C3AED"],
    )
    fig.update_layout(
        title=f"Model Accuracy: {target_name}",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        xaxis={"showgrid": True, "gridcolor": "#F1F5F9"},
        yaxis={"showgrid": True, "gridcolor": "#F1F5F9"},
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
            marker={
                "size": 6,
                "color": "#8B5CF6",
                "symbol": "diamond"
            },
            name="Wind Chill",
            hovertemplate="<b>AVG Wind Chill</b><br>%{y:.1f}°C<extra></extra>"
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
