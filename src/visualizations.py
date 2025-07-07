import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st


def map_visualization(df):
    df_copy = df.copy()
    if "city" not in df_copy.columns:
        return go.Figure(layout={"title": "Missing 'city' column in data."})

    required_cols = {'city', 'lat', 'lon', 'temp_avg', 'energy_demand_MW'}
    if df_copy.empty or not required_cols.issubset(df_copy.columns):
        fig = go.Figure(go.Scattermapbox())
        fig.update_layout(mapbox_style="open-street-map", title="Geographic Overview (No data to display)")
        return fig

    map_summary = df_copy.groupby('city').agg(
        lat=('lat', 'first'),
        lon=('lon', 'first'),
        avg_temp=('temp_avg', 'mean'),
        avg_demand=('energy_demand_MW', 'mean')
    ).reset_index()

    fig = px.scatter_mapbox(
        map_summary,
        lat="lat",
        lon="lon",
        size="avg_demand",
        color="avg_temp",
        hover_name="city",
        hover_data={"avg_temp": ":.1f °F", "avg_demand": ":.0f MW", "lat": False, "lon": False},
        color_continuous_scale=px.colors.sequential.Plasma,
        size_max=30,
        zoom=3,
        height=500,
        title="Geographic Overview: Avg. Demand (Size) & Avg. Temp (Color)"
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title="Avg Temp (°F)")
    )
    return fig


def dual_axis_time_series(df, location):
    df = df.copy()
    required_columns = {'date', 'temp_avg', 'energy_demand_MW'}
    if df.empty or not required_columns.issubset(df.columns):
        fig = go.Figure()
        fig.update_layout(title=f"{location} - Not enough data for time series")
        return fig

    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

    df = df.sort_values("date")

    fig = go.Figure()

    # Shade weekends
    df_weekends = df[df['date'].dt.dayofweek >= 5]
    for i in range(len(df_weekends)):
        fig.add_vrect(
            x0=df_weekends['date'].iloc[i] - pd.Timedelta(days=0.5),
            x1=df_weekends['date'].iloc[i] + pd.Timedelta(days=0.5),
            fillcolor="rgba(200, 200, 200, 0.2)",
            layer="below",
            line_width=0
        )

    # Add traces
    fig.add_trace(go.Scatter(x=df["date"], y=df["temp_avg"], mode='lines', name='Temperature (°F)'))
    fig.add_trace(go.Scatter(x=df["date"], y=df["energy_demand_MW"], mode='lines',
                             name='Energy Demand (MW)', yaxis='y2', line=dict(dash='dot')))

    fig.update_layout(
        yaxis=dict(title="Temperature (°F)"),
        yaxis2=dict(title="Energy Demand (MW)", overlaying='y', side='right'),
        title=f"{location} - Temperature vs Energy Demand",
        xaxis_title="Date",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def correlation_plot(df):
    df = df.copy()
    if "city" not in df.columns:
        return px.scatter(title="Missing 'city' column for correlation analysis.")

    required_cols = {'temp_avg', 'energy_demand_MW', 'city', 'date'}
    if df.empty or not required_cols.issubset(df.columns):
        return px.scatter(title="No data available for correlation analysis.")

    df_cleaned = df.dropna(subset=['temp_avg', 'energy_demand_MW'])
    if df_cleaned.empty:
        return px.scatter(title="No data available for correlation analysis.")

    fig = px.scatter(
        df_cleaned, x="temp_avg", y="energy_demand_MW", color="city", hover_data=["date"],
        trendline="ols", trendline_color_override="black"
    )

    results = px.get_trendline_results(fig)
    r_squared = None

    if not results.empty:
        fit = results.iloc[0]["px_fit_results"]
        r_squared = fit.rsquared
        intercept = fit.params[0]
        slope = fit.params[1]
        equation = f"y = {slope:.2f}x + {intercept:.2f}"

        # Add annotation inside the plot
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.05, y=0.95,
            text=f"{equation}, R²={r_squared:.3f}",
            showarrow=False,
            font=dict(size=12, color="black"),
            bgcolor="rgba(255,255,255,0.7)"
        )

        # Streamlit info banner
        if r_squared >= 0.7:
            msg = "🌟 Strong correlation"
        elif r_squared >= 0.4:
            msg = "📈 Moderate correlation"
        else:
            msg = "🔍 Weak correlation"
        st.success(f"R-squared: {r_squared:.3f} — {msg}")

    else:
        st.warning("No fit results available for this selection.")

    title_text = "Temperature vs Energy Demand Correlation"
    if r_squared is not None:
        title_text += f" (R² = {r_squared:.3f})"

    fig.update_layout(
        title=title_text,
        xaxis_title="Average Temperature (°F)",
        yaxis_title="Energy Demand (MW)"
    )
    return fig


def heatmap_usage_pattern(df):
    df = df.copy()
    required = {'date', 'temp_avg', 'energy_demand_MW'}
    if df.empty or not required.issubset(df.columns):
        return go.Figure(layout={"title": "Heatmap not available — missing required data."})

    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

    df["weekday"] = df["date"].dt.day_name()
    df["temp_band"] = pd.cut(
        df["temp_avg"],
        bins=[-999, 50, 60, 70, 80, 90, 999],
        labels=["<50°F", "50-60°F", "60-70°F", "70-80°F", "80-90°F", ">90°F"]
    )

    pivot = df.pivot_table(index="temp_band", columns="weekday", values="energy_demand_MW", aggfunc="mean")
    pivot = pivot.dropna(how="all", axis=1).dropna(how="all", axis=0)

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex(columns=[day for day in weekday_order if day in pivot.columns])

    if pivot.empty:
        return go.Figure(layout={"title": "No data available for this heatmap selection."})

    fig = px.imshow(
        pivot,
        text_auto=".0f",
        color_continuous_scale="YlOrRd",
        aspect="auto"
    )
    fig.update_layout(
        title="Average Energy Demand (MW) by Temp Range and Day of Week",
        coloraxis_colorbar=dict(title="Demand (MW)")
    )
    return fig
