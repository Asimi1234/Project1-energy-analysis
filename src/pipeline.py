# === BEGINNING OF SCRIPT: Unchanged imports and constants ===
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from re import match

# Add error handling for missing analysis module
try:
    from analysis import generate_quality_report
except ImportError:
    print("Warning: analysis module not found. Quality reports will be skipped.")
    generate_quality_report = None

from config.constants import CITY_TIMEZONE_MAP, CITY_COORDS_MAP

PROJECT_ROOT = Path(__file__).resolve().parent.parent
raw_data_path = PROJECT_ROOT / "data/raw"
processed_data_path = PROJECT_ROOT / "data/processed"
report_path = PROJECT_ROOT / "data/reports"

processed_data_path.mkdir(parents=True, exist_ok=True)
report_path.mkdir(parents=True, exist_ok=True)

all_files = [f for f in raw_data_path.rglob("*") if f.is_file() and f.suffix in {".csv", ".json"}]
if not all_files:
    print("No raw data files found.")
    exit()

energy_dfs = []
weather_dfs = []

def clean_city_name(city_name):
    """Standardize city name formatting"""
    return city_name.strip().title() if city_name else "Unknown"

# === LOAD ALL RAW FILES ===
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

            # Handle period column
            if 'period' in df.columns and df['period'].notnull().any():
                df['period_dt'] = pd.to_datetime(df['period'], errors='coerce')

            # Handle date column
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')

            # Use period as fallback for date if needed
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

        # Extract city name from filename
        match_city = match(r"(energy|weather)_(.+?)_\d{4}-\d{2}-\d{2}", file.stem)
        if match_city:
            city_name = clean_city_name(match_city.group(2))
        else:
            print(f"Unable to extract city from filename {file.name}")
            continue

        df["city"] = city_name

        # Categorize files
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

# === DATE STAMP FOR TODAY ===
today_str = datetime.now().strftime("%Y_%m_%d")

# === PROCESS ENERGY DATA ===
energy_dfs = [df for df in energy_dfs if 'date' in df.columns]
if energy_dfs:
    energy_df = pd.concat(energy_dfs, ignore_index=True)
    energy_df.dropna(subset=['date'], inplace=True)
    energy_df['date'] = pd.to_datetime(energy_df['date'], errors='coerce')
    energy_df.dropna(subset=['date'], inplace=True)

    # Fix column naming issues
    if 'value' in energy_df.columns and 'energy_demand_MW' not in energy_df.columns:
        energy_df.rename(columns={'value': 'energy_demand_MW'}, inplace=True)

    # Fix typo in column name
    if "responndent-name" in energy_df.columns:
        energy_df.rename(columns={"responndent-name": "respondent-name"}, inplace=True)
    # Also check for the correct spelling
    if "respondent-name" in energy_df.columns:
        energy_df.rename(columns={"respondent-name": "respondent_name"}, inplace=True)

    # Clean up columns
    if "timezone-description" in energy_df.columns:
        energy_df.drop(columns=["timezone-description"], inplace=True)

    # Standardize city names
    energy_df["city"] = energy_df["city"].apply(clean_city_name)

    # === LOAD EXISTING PROCESSED ENERGY FILE ===
    master_energy_path = processed_data_path / "energy_master.csv"
    if master_energy_path.exists():
        existing_energy = pd.read_csv(master_energy_path, parse_dates=["date"])
    else:
        existing_energy = pd.DataFrame(columns=energy_df.columns)

    combined_energy = pd.concat([existing_energy, energy_df], ignore_index=True)
    combined_energy.drop_duplicates(subset=["city", "date"], keep="last", inplace=True)
    combined_energy.to_csv(master_energy_path, index=False)

    processed_energy_file = processed_data_path / f"processed_energy_data_{today_str}.csv"
    combined_energy.to_csv(processed_energy_file, index=False)
    print(f"Processed energy data saved to {processed_energy_file}")
    # Save a permanent backup
    combined_energy.to_csv(processed_data_path / "backup_energy.csv", index=False)

else:
    print("No valid energy data files found.")
    combined_energy = pd.DataFrame()

# === PROCESS WEATHER DATA ===
if weather_dfs:
    weather_df = pd.concat(weather_dfs, ignore_index=True)
    weather_df.dropna(subset=['date'], inplace=True)
    weather_df['date'] = pd.to_datetime(weather_df['date'], errors='coerce')
    weather_df.dropna(subset=['date'], inplace=True)

    # Fix column naming
    if "tempp_max_F" in weather_df.columns:
        weather_df.rename(columns={"tempp_max_F": "temp_max_F"}, inplace=True)

    # Calculate average temperature if missing
    if ("temp_avg" not in weather_df.columns and 
        "temp_max_F" in weather_df.columns and 
        "temp_min_F" in weather_df.columns):
        weather_df["temp_avg"] = (weather_df["temp_max_F"] + weather_df["temp_min_F"]) / 2

    # Standardize city names
    weather_df["city"] = weather_df["city"].apply(clean_city_name)

    # === LOAD EXISTING PROCESSED WEATHER FILE ===
    master_weather_path = processed_data_path / "weather_master.csv"
    if master_weather_path.exists():
        existing_weather = pd.read_csv(master_weather_path, parse_dates=["date"])
    else:
        existing_weather = pd.DataFrame(columns=weather_df.columns)

    combined_weather = pd.concat([existing_weather, weather_df], ignore_index=True)
    combined_weather.drop_duplicates(subset=["city", "date"], keep="last", inplace=True)
    combined_weather.to_csv(master_weather_path, index=False)

    processed_weather_file = processed_data_path / f"processed_weather_data_{today_str}.csv"
    combined_weather.to_csv(processed_weather_file, index=False)
    print(f"Processed weather data saved to {processed_weather_file}")
    # Save permanent weather backup
    combined_weather.to_csv(processed_data_path / "backup_weather.csv", index=False)

else:
    print("No valid weather data files found.")
    master_weather_path = processed_data_path / "weather_master.csv"
    if master_weather_path.exists():
        combined_weather = pd.read_csv(master_weather_path, parse_dates=["date"])
        print("Using existing master weather data for backup.")
        combined_weather.to_csv(processed_data_path / "backup_weather.csv", index=False)
    else:
        combined_weather = pd.DataFrame()
        print("No weather data available at all.")

# === MERGE AND SAVE COMBINED DATA ===
if not combined_energy.empty and not combined_weather.empty:
    try:
        merge_cols = ["date", "city"]
        print(f"Merging dataframes on columns: {merge_cols}")

        combined_energy["date"] = pd.to_datetime(combined_energy["date"])
        combined_weather["date"] = pd.to_datetime(combined_weather["date"])

        # === MERGE DATA ===
        merged_df = pd.merge(combined_energy, combined_weather, on=merge_cols, how="inner")

        # Handle timezone columns after merge
        if "timezone_y" in merged_df.columns:
            if "timezone_x" in merged_df.columns:
                merged_df.drop(columns=["timezone_x"], inplace=True)
            merged_df.rename(columns={"timezone_y": "timezone"}, inplace=True)

        # Ensure required columns exist
        for col in ["precipitation", "temp_max_F", "temp_min_F", "timezone"]:
            if col not in merged_df.columns:
                merged_df[col] = pd.NA

        # Convert to numeric
        for col in ["temp_max_F", "temp_min_F", "precipitation"]:
            if col in merged_df.columns:
                merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
                   
        # Calculate temperature average
        if "temp_max_F" in merged_df.columns and "temp_min_F" in merged_df.columns:
            merged_df["temp_avg"] = merged_df[["temp_max_F", "temp_min_F"]].mean(axis=1)
        
        merged_df["weather_available"] = merged_df.get("temp_avg", pd.Series(dtype=float)).notna()

        # Add coordinates with better error handling
        def get_coord(city, coord_type):
            city_data = CITY_COORDS_MAP.get(city, {})
            if isinstance(city_data, dict):
                return city_data.get(coord_type)
            return None

        merged_df["lat"] = merged_df["city"].apply(lambda c: get_coord(c, "lat"))
        merged_df["lon"] = merged_df["city"].apply(lambda c: get_coord(c, "lon"))

        merged_file = processed_data_path / f"processed_merged_data_{today_str}.csv"
        merged_df.to_csv(merged_file, index=False)
        print(f"Merged data saved to {merged_file}")

    except Exception as e:
        print(f"Failed to merge energy and weather data: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print("Skipping merge — one or both datasets are missing.")

# === GENERATE QUALITY REPORTS ===
if generate_quality_report is not None:
    # Weather quality report
    if not combined_weather.empty:
        try:
            weather_report = generate_quality_report(
                combined_weather,
                temp_cols=["temp_min_F", "temp_max_F"],
                energy_col="energy_demand_MW",
                date_col="date"
            )
            with open(report_path / f"quality_report_weather_{today_str}.json", "w") as f:
                json.dump(weather_report, f, indent=2)
            print("Weather quality report saved.")
        except Exception as e:
            print(f"Failed to generate weather quality report: {e}")
    else:
        print("No weather data to check quality.")

    # Energy quality report
    if not combined_energy.empty:
        try:
            # Check which temperature columns exist in energy data
            available_temp_cols = [col for col in ["temp_min_F", "temp_max_F"] if col in combined_energy.columns]
            
            energy_report = generate_quality_report(
                combined_energy,
                temp_cols=available_temp_cols,
                energy_col="energy_demand_MW",
                date_col="date"
            )
            with open(report_path / f"quality_report_energy_{today_str}.json", "w") as f:
                json.dump(energy_report, f, indent=2)
            print("Energy quality report saved.")
        except Exception as e:
            print(f"Failed to generate energy quality report: {e}")
    else:
        print("No energy data to check quality.")
else:
    print("Quality report function not available - skipping reports.")