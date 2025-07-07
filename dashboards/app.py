import streamlit as st
import pandas as pd
import json
from pathlib import Path

# Import visualizations
from src.visualizations import (
    map_visualization,
    dual_axis_time_series,
    correlation_plot,
    heatmap_usage_pattern,
    seasonal_demand_trend,          # ✅ NEW
    regional_correlation_bar        # ✅ NEW
)

# --- Page Config ---
st.set_page_config(page_title="Energy & Weather Analysis", layout="wide")

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def find_latest_file(directory, pattern):
    dir_path = Path(directory)
    if not dir_path.exists():
        return None
    files = list(dir_path.glob(pattern))
    return max(files, key=lambda p: p.stat().st_mtime) if files else None

@st.cache_data
def load_data(data_type):
    pattern = f"processed_{data_type}_data_*.csv"
    report_pattern = f"quality_report_{data_type}_*.json"

    latest_data_file = find_latest_file(PROJECT_ROOT / "data/processed", pattern)
    if latest_data_file is None:
        return None, None

    try:
        df = pd.read_csv(latest_data_file)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        else:
            df["date"] = pd.NaT

        if "temp_avg" not in df.columns and "temp_max_F" in df.columns and "temp_min_F" in df.columns:
            df["temp_avg"] = (df["temp_max_F"] + df["temp_min_F"]) / 2
    except Exception as e:
        st.warning(f"Failed to load {data_type} data: {e}")
        df = None

    report = None
    latest_report_file = find_latest_file(PROJECT_ROOT / "data/reports", report_pattern)
    if latest_report_file and latest_report_file.exists():
        try:
            with open(latest_report_file, 'r') as f:
                report = json.load(f)
        except Exception as e:
            st.warning(f"Failed to load report: {e}")

    return df, report

@st.cache_data
def load_merged_data():
    merged_file = find_latest_file(PROJECT_ROOT / "data/processed", "processed_merged_data_*.csv")
    if merged_file:
        try:
            df = pd.read_csv(merged_file)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df
        except Exception as e:
            st.warning(f"Failed to load merged file: {e}")
    return None


def display_quality_report(report):
    if not report:
        st.warning("No quality report found.")
        return

    freshness = report.get("freshness", {})
    fresh_status = "✅ Fresh" if freshness.get("is_fresh") else "❌ Stale"
    st.metric(
        label="Data Freshness",
        value=fresh_status,
        help=f"Latest date: {freshness.get('latest_date', 'N/A')} ({freshness.get('days_ago', '?')} days ago)"
    )

    col1, col2 = st.columns(2)
    
    def recursive_sum(d):
        total = 0
        for v in d.values():
            if isinstance(v, dict):
                total += recursive_sum(v)
            elif isinstance(v, (int, float)):
                total += v
            # else ignore or handle other types if needed
        return total

    with col1:
        st.subheader("Missing Values")
        missing_df = pd.DataFrame.from_dict(report.get("missing_values", {}), orient="index", columns=["Count"])
        total_missing = missing_df["Count"].sum()
        if total_missing == 0:
            st.success("✅ No missing values.")
        else:
            st.warning(f"{total_missing} missing values found.")
            st.dataframe(missing_df[missing_df["Count"] > 0])

    with col2:
        st.subheader("Outlier Detection")
        outliers = report.get("outliers", {})
        total_outliers = recursive_sum(outliers)
        if total_outliers == 0:
            st.success("✅ No outliers.")
        else:
            st.warning(f"{total_outliers} outliers detected.")
            st.json(outliers)

# --- MAIN APP ---
st.title("Energy Demand & Weather Correlation Dashboard")

energy_df, energy_report = load_data("energy")
weather_df, weather_report = load_data("weather")
merged_df = load_merged_data()

DEBUG = False

if DEBUG and merged_df is not None:
    st.write("✅ Loaded merged data with shape:", merged_df.shape)
    st.write("🧪 Columns:", merged_df.columns.tolist())
    st.write(f"Missing timezones: {merged_df['timezone'].isna().sum()}")
    st.write(f"Missing or invalid dates: {merged_df['date'].isna().sum()}")
    st.dataframe(merged_df.head())

if merged_df is not None:
    if DEBUG:
        st.info("Loaded pre-merged dataset.")
else:
    if energy_df is not None and weather_df is not None:
        try:
            merged_df = pd.merge(
                energy_df,
                weather_df,
                on=["date", "city", "timezone"],
                how="left"
            )
            if DEBUG:
                st.info("Merged energy + weather data.")
        except Exception as e:
            if DEBUG:
                st.warning(f"Merge failed: {e}")
            merged_df = energy_df if energy_df is not None else weather_df
    else:
        merged_df = energy_df if energy_df is not None else weather_df
        if merged_df is not None:
            if DEBUG:
                st.info("Using only one data source.")
        else:
            st.error("No usable dataset could be loaded. Run pipeline first.")
            st.stop()

# --- Tabs ---
tab1, tab2 = st.tabs(["📈 Analysis Dashboard", "🛡️ Data Quality Reports"])

with tab1:
    st.sidebar.header("Filters")

    if "city" not in merged_df.columns or merged_df["date"].isna().all():
        st.error("❌ Data is missing critical columns like `city` or valid dates.")
        st.stop()

    merged_df["city"] = merged_df["city"].astype(str)
    cities = sorted(merged_df["city"].dropna().unique().tolist())
    selected_cities = st.sidebar.multiselect("Select Cities", cities, default=cities)

    if merged_df["date"].notna().any():
        min_date = merged_df["date"].min().date()
        max_date = merged_df["date"].max().date()
    else:
        st.error("No valid dates in data.")
        st.stop()

    selected_range = st.sidebar.date_input(
        "Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
        if start_date > end_date:
            st.warning("⚠️ Start date must be before end date.")
            st.stop()
    else:
        st.error("Invalid date range selected.")
        st.stop()

    filtered_df = merged_df[
        (merged_df["city"].isin(selected_cities)) &
        (merged_df["date"].dt.date >= start_date) &
        (merged_df["date"].dt.date <= end_date)
    ]

    if filtered_df.empty:
        st.warning("⚠️ No data available for the selected filters.")
        st.stop()

    latest_update = merged_df["date"].max()
    if pd.notna(latest_update):
        st.info(f"📅 Latest Data: {latest_update.date()}")

    st.header("🗺️ Geographic Overview")
    st.plotly_chart(map_visualization(filtered_df), use_container_width=True)
    # Compute quartiles for demand thresholds dynamically

    if "demand_today" in filtered_df.columns:
        q1 = filtered_df["demand_today"].quantile(0.25)
        q3 = filtered_df["demand_today"].quantile(0.75)
    elif "energy_demand_MW" in filtered_df.columns:
        q1 = filtered_df["energy_demand_MW"].quantile(0.25)
        q3 = filtered_df["energy_demand_MW"].quantile(0.75)
    else:
        q1, q3 = 40, 79  # fallback values if none found

    caption_text = (
        f"🟢 Green: Low demand (< {q1:.1f} MW) &nbsp;&nbsp;"
        f"🟠 Orange: Moderate demand ({q1:.1f} - {q3:.1f} MW) &nbsp;&nbsp;"
        f"🔴 Red: High demand (≥ {q3:.1f} MW) &nbsp;&nbsp;"
        f"⚪ Gray: No data available for today."
    )

    st.caption(caption_text)


    st.header("Detailed Analysis")

    if "temp_avg" not in filtered_df.columns:
        st.warning("⚠️ Missing `temp_avg` column. Skipping temperature visualizations.")
    else:
        for loc in selected_cities:
            st.subheader(f"📊 {loc} - Time Series")
            loc_df = filtered_df[filtered_df["city"] == loc]
            st.plotly_chart(dual_axis_time_series(loc_df, loc), use_container_width=True)
            
            st.caption("🔴 Light red shaded regions indicate weekends.")

        st.subheader("📈 Correlation Plot (Pearson R)")
        st.plotly_chart(correlation_plot(filtered_df), use_container_width=True)

        st.subheader("📊 Regional Pearson R Comparison")
        st.plotly_chart(regional_correlation_bar(filtered_df), use_container_width=True)

        st.subheader("📊 Seasonal Energy Demand Trend")
        st.plotly_chart(seasonal_demand_trend(filtered_df), use_container_width=True)

        if "energy_demand_MW" in filtered_df.columns:
            st.subheader("📊 Energy Usage Pattern Heatmap")
            st.plotly_chart(heatmap_usage_pattern(filtered_df), use_container_width=True)
        else:
            st.warning("⚠️ Missing `energy_demand_MW`. Skipping heatmap.")

with tab2:
    st.subheader("📉 Energy Data Report")
    display_quality_report(energy_report)

    st.subheader("🌦️ Weather Data Report")
    display_quality_report(weather_report)
