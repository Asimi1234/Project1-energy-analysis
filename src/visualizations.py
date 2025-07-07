import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import statsmodels.api as sm
from scipy.stats import pearsonr
import numpy as np


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

    df_weekends = df[df['date'].dt.dayofweek >= 5]
    for i in range(len(df_weekends)):
        fig.add_vrect(
            x0=df_weekends['date'].iloc[i] - pd.Timedelta(days=0.5),
            x1=df_weekends['date'].iloc[i] + pd.Timedelta(days=0.5),
            fillcolor="rgba(200, 200, 200, 0.2)",
            layer="below",
            line_width=0
        )

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

    import numpy as np
    from scipy.stats import pearsonr

    # Compute per-city r values
    st.subheader("📊 Per-City Pearson R Values")
    city_rs = {}
    for city in df_cleaned["city"].unique():
        city_data = df_cleaned[df_cleaned["city"] == city]
        if len(city_data) > 1:
            r, _ = pearsonr(city_data["temp_avg"], city_data["energy_demand_MW"])
            city_rs[city] = r
            # Annotate per r value
            if r >= 0.7:
                st.success(f"{city}: {r:.3f} — ✅ Strong correlation")
            elif r >= 0.4:
                st.info(f"{city}: {r:.3f} — 📈 Moderate correlation")
            else:
                st.warning(f"{city}: {r:.3f} — 🔍 Weak correlation")
        else:
            st.warning(f"{city}: Not enough data for correlation.")

    # Compute global Pearson r
    if len(df_cleaned) > 1:
        global_r, _ = pearsonr(df_cleaned["temp_avg"], df_cleaned["energy_demand_MW"])
        if global_r >= 0.7:
            st.success(f"🔍 Global Pearson R: {global_r:.3f} — ✅ Strong correlation")
        elif global_r >= 0.4:
            st.info(f"🔍 Global Pearson R: {global_r:.3f} — 📈 Moderate correlation")
        else:
            st.warning(f"🔍 Global Pearson R: {global_r:.3f} — 🔍 Weak correlation")
    else:
        st.warning("Not enough data for global correlation.")

    # Scatter plot with trendline
    fig = px.scatter(
        df_cleaned, x="temp_avg", y="energy_demand_MW", color="city", hover_data=["date"],
        trendline="ols", trendline_color_override="black"
    )

    fig.update_layout(
        title="Temperature vs Energy Demand Correlation (with OLS Trendline)",
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

def seasonal_demand_trend(df):
    df = df.copy()
    if 'date' not in df.columns or 'energy_demand_MW' not in df.columns:
        return go.Figure(layout={"title": "Seasonal trend unavailable — missing data."})

    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

    df['month'] = df['date'].dt.month_name()
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    monthly_avg = df.groupby('month')["energy_demand_MW"].mean().reindex(month_order)

    fig = px.line(
        x=monthly_avg.index,
        y=monthly_avg.values,
        labels={"x": "Month", "y": "Avg Energy Demand (MW)"},
        markers=True,
        title="Seasonal Energy Demand Pattern"
    )
    return fig

def regional_correlation_bar(df):
    df_cleaned = df.dropna(subset=["temp_avg", "energy_demand_MW", "city"])
    if df_cleaned.empty:
        return go.Figure(layout={"title": "No data available for regional correlation analysis."})

    corrs = []
    for city in df_cleaned["city"].unique():
        city_df = df_cleaned[df_cleaned["city"] == city]
        if len(city_df) > 1:
            r, _ = pearsonr(city_df["temp_avg"], city_df["energy_demand_MW"])
            corrs.append({"city": city, "r_value": r})

    corr_df = pd.DataFrame(corrs).sort_values(by="r_value", ascending=False)

    fig = px.bar(
        corr_df,
        x="city",
        y="r_value",
        color="r_value",
        color_continuous_scale="Bluered",
        text="r_value",
        title="Per-City Pearson R Correlation (Temp vs Demand)"
    )
    fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    fig.update_layout(
        yaxis_title="Pearson R",
        coloraxis_colorbar=dict(title="R Value"),
        uniformtext_minsize=8, uniformtext_mode='hide'
    )
    return fig
