import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from re import match

# --- Constants ---
from config.constants import CITY_TIMEZONE_MAP, CITY_COORDS_MAP

# --- Setup paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
raw_data_path = PROJECT_ROOT / "data/raw"
processed_data_path = PROJECT_ROOT / "data/processed"
report_path = PROJECT_ROOT / "data/reports"

processed_data_path.mkdir(parents=True, exist_ok=True)
report_path.mkdir(parents=True, exist_ok=True)

# --- Collect files ---
all_files = list(raw_data_path.glob("*.*"))
if not all_files:
    print("No raw data files found.")
    exit()

energy_dfs = []
weather_dfs = []

for file in all_files:
    try:
        if file.suffix == ".json":
            with open(file, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'results' in data:
                print(f"Skipping raw API response file: {file.name}")
                continue
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if "response" in data and "data" in data["response"]:
                    df = pd.DataFrame(data["response"]["data"])
                else:
                    df = pd.DataFrame([data])
            else:
                print(f"Unknown JSON format in {file.name}, skipping.")
                continue

        elif file.suffix == ".csv":
            df = pd.read_csv(file, encoding='utf-8-sig')
            print(f"Columns in {file.name}: {df.columns.tolist()}")

            # --- UPDATED DATE/PERIOD HANDLING ---
            if 'period' in df.columns:
                if df['period'].notnull().any():
                    df['period_dt'] = pd.to_datetime(df['period'], errors='coerce')

            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')

            if 'date' not in df.columns or df['date'].isnull().all():
                if 'period_dt' in df.columns and df['period_dt'].notnull().any():
                    df['date'] = df['period_dt']
                    print(f"Using 'period' as fallback for 'date' in {file.name}")
                else:
                    print(f"Skipping {file.name} — missing usable 'date' and 'period'")
                    continue

        else:
            print(f"Skipping unsupported file type: {file.name}")
            continue

        # --- Extract city from filename ---
        match_city = match(r"(energy|weather)_(.+?)_\d{4}-\d{2}-\d{2}", file.stem)
        if match_city:
            city_name = match_city.group(2).strip().title()
        else:
            print(f"Unable to extract city from filename {file.name}")
            continue

        df["city"] = city_name

        # --- Classify ---
        if file.name.startswith("weather_"):
            timezone = CITY_TIMEZONE_MAP.get(city_name, "Unknown")
            df["timezone"] = timezone
            weather_dfs.append(df)
        elif file.name.startswith("energy_"):
            energy_dfs.append(df)
        else:
            print(f"Skipping unrelated file: {file.name}")

    except Exception as e:
        print(f"Error processing {file.name}: {e}")

# --- Process Energy Data ---
today_str = datetime.now().strftime("%Y_%m_%d")

energy_dfs = [df for df in energy_dfs if 'date' in df.columns]  # extra safeguard
if energy_dfs:
    energy_df = pd.concat(energy_dfs, ignore_index=True)
    energy_df.dropna(subset=['date'], inplace=True)
    energy_df['date'] = pd.to_datetime(energy_df['date'], errors='coerce')
    energy_df.dropna(subset=['date'], inplace=True)

    if 'value' in energy_df.columns and 'energy_demand_MW' not in energy_df.columns:
        energy_df.rename(columns={'value': 'energy_demand_MW'}, inplace=True)

    if "responndent-name" in energy_df.columns:
        energy_df.rename(columns={"responndent-name": "respondent-name"}, inplace=True)

    if "timezone-description" in energy_df.columns:
        energy_df.drop(columns=["timezone-description"], inplace=True)

    energy_df["city"] = energy_df["city"].str.strip().str.title()
    energy_df = energy_df.drop_duplicates(subset=["city", "date"])

    print(f"Columns in energy_df before merge: {energy_df.columns.tolist()}")

    if 'value-units' in energy_df.columns:
        unique_units = energy_df['value-units'].dropna().unique()
        if len(unique_units) > 1:
            print(f"Multiple energy units found: {unique_units}")
        else:
            print(f"Energy units used: {unique_units[0]}")

    if "energy_demand_MW" not in energy_df.columns:
        print("Could not find energy demand column in energy data. Filling with NaN.")
        energy_df["energy_demand_MW"] = None

    processed_energy_file = processed_data_path / f"processed_energy_data_{today_str}.csv"
    energy_df.to_csv(processed_energy_file, index=False)
    print(f"Processed energy data saved to {processed_energy_file}")

    # --- Energy Quality Report ---
    missing_values = energy_df.isnull().sum().to_dict()
    outliers = {}
    if "energy_demand_MW" in energy_df.columns:
        q1 = energy_df["energy_demand_MW"].quantile(0.25)
        q3 = energy_df["energy_demand_MW"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers["energy_demand_MW"] = int(((energy_df["energy_demand_MW"] < lower) | (energy_df["energy_demand_MW"] > upper)).sum())

    try:
        latest_date = energy_df["date"].max()
        days_ago = (datetime.now().date() - latest_date.date()).days
        is_fresh = days_ago <= 1
    except Exception:
        latest_date, days_ago, is_fresh = None, None, False

    report = {
        "missing_values": missing_values,
        "outliers": outliers,
        "freshness": {
            "latest_date": str(latest_date) if latest_date else "N/A",
            "days_ago": days_ago,
            "is_fresh": is_fresh
        }
    }

    report_file = report_path / f"quality_report_energy_{today_str}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=4)

    print(f"Energy data quality report saved to {report_file}")
else:
    print("No valid energy data files found.")
    energy_df = pd.DataFrame()

# --- Process Weather Data ---
if weather_dfs:
    weather_df = pd.concat(weather_dfs, ignore_index=True)
    weather_df.dropna(subset=['date'], inplace=True)
    weather_df['date'] = pd.to_datetime(weather_df['date'], errors='coerce')
    weather_df.dropna(subset=['date'], inplace=True)

    if "tempp_max_F" in weather_df.columns:
        weather_df.rename(columns={"tempp_max_F": "temp_max_F"}, inplace=True)

    if "temp_avg" not in weather_df.columns and "temp_max_F" in weather_df.columns and "temp_min_F" in weather_df.columns:
        weather_df["temp_avg"] = (weather_df["temp_max_F"] + weather_df["temp_min_F"]) / 2

    weather_df["city"] = weather_df["city"].str.strip().str.title()

    print(f"Columns in weather_df before merge: {weather_df.columns.tolist()}")

    processed_weather_file = processed_data_path / f"processed_weather_data_{today_str}.csv"
    weather_df.to_csv(processed_weather_file, index=False)
    print(f"Processed weather data saved to {processed_weather_file}")

    missing_values = weather_df.isnull().sum().to_dict()
    outliers = {}
    for col in ["temp_max_F", "temp_min_F", "temp_avg"]:
        if col in weather_df.columns:
            q1 = weather_df[col].quantile(0.25)
            q3 = weather_df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
    
            # IQR-based outliers
            iqr_mask = (weather_df[col] < lower) | (weather_df[col] > upper)
            iqr_count = int(iqr_mask.sum())
    
            # Rule-based outliers
            rule_mask = (weather_df[col] > 130) | (weather_df[col] < -50)
            rule_count = int(rule_mask.sum())
    
            # Store both in nested dict
            outliers[col] = {
                "iqr": iqr_count,
                "rule_based": rule_count
            }
    
            # --- Debug output
            print(f"[DEBUG] Outliers in '{col}': IQR={iqr_count}, Rule-based={rule_count}")
            print(f"[DEBUG] IQR bounds for '{col}': lower={lower}, upper={upper}")
    
            if iqr_count > 0:
                print(f"[DEBUG] IQR Outlier rows in '{col}':")
                print(weather_df[iqr_mask][['date', 'city', col]])
    
            if rule_count > 0:
                print(f"[DEBUG] Rule-based Outlier rows in '{col}':")
                print(weather_df[rule_mask][['date', 'city', col]])

    try:
        latest_date = weather_df["date"].max()
        days_ago = (datetime.now().date() - latest_date.date()).days
        is_fresh = days_ago <= 3
    except Exception:
        latest_date, days_ago, is_fresh = None, None, False

    report = {
        "missing_values": missing_values,
        "outliers": outliers,
        "freshness": {
            "latest_date": str(latest_date) if latest_date else "N/A",
            "days_ago": days_ago,
            "is_fresh": is_fresh
        }
    }

    report_file = report_path / f"quality_report_weather_{today_str}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=4)

    print(f"Weather data quality report saved to {report_file}")
else:
    print("No valid weather data files found.")
    weather_df = pd.DataFrame()

# --- Merge and Save Combined Data ---
if not energy_df.empty and not weather_df.empty:
    try:
        merge_cols = ["date", "city"]
        print(f"Merging dataframes on columns: {merge_cols}")

        # Ensure consistent date formats
        energy_df["date"] = pd.to_datetime(energy_df["date"]).dt.date
        weather_df["date"] = pd.to_datetime(weather_df["date"]).dt.date

        # Merge while keeping all energy rows
        merged_df = pd.merge(energy_df, weather_df, on=merge_cols, how="left")

        print(f"Number of merged rows: {len(merged_df)}")
        print(f"Columns in merged_df: {merged_df.columns.tolist()}")

        # Handle timezone column conflict if present
        if "timezone_y" in merged_df.columns:
            merged_df.drop(columns=["timezone_x"], inplace=True)
            merged_df.rename(columns={"timezone_y": "timezone"}, inplace=True)

        # Ensure weather-related columns exist
        weather_columns = ["precipitation", "temp_max_F", "temp_min_F", "timezone"]
        for col in weather_columns:
            if col not in merged_df.columns:
                merged_df[col] = pd.NA

        # Ensure weather columns are numeric
        for col in ["temp_max_F", "temp_min_F", "precipitation"]:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        
        # Compute temperature average
        merged_df["temp_avg"] = merged_df[["temp_max_F", "temp_min_F"]].mean(axis=1)
        
        # Mark rows with valid weather
        merged_df["weather_available"] = merged_df["temp_avg"].notna()


        # Add lat/lon from static city coordinates
        merged_df["lat"] = merged_df["city"].map(lambda c: CITY_COORDS_MAP.get(c, {}).get("lat"))
        merged_df["lon"] = merged_df["city"].map(lambda c: CITY_COORDS_MAP.get(c, {}).get("lon"))

        # Save merged data
        merged_file = processed_data_path / f"processed_merged_data_{today_str}.csv"
        merged_df.to_csv(merged_file, index=False)
        print(f"Merged data saved to {merged_file}")

    except Exception as e:
        print(f"Failed to merge energy and weather data: {e}")
else:
    print("Skipping merge — one or both datasets are missing.")
