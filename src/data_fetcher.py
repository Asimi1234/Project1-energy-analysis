import requests
import pandas as pd
import logging
import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
Path("logs").mkdir(exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
    )

# Load config
CONFIG_PATH = Path("config/config.yaml")

def load_config():
    """Load configuration from YAML file with error handling."""
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {CONFIG_PATH}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Error parsing config file: {e}")
        raise

config = load_config()

# Load API keys from environment variables
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
EIA_API_KEY = os.getenv("EIA_API_KEY")

if not NOAA_API_KEY or not EIA_API_KEY:
    raise ValueError("API keys not found in .env file. Please set NOAA_API_KEY and EIA_API_KEY")

def create_directories():
    """Create necessary directories."""
    directories = [
        Path("data/raw"),
        Path("data/backup"),
        Path("logs")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create city-specific directories
    for city in config['cities']:
        city_dir = Path(f"data/raw/{city['name']}")
        city_dir.mkdir(parents=True, exist_ok=True)

def fetch_weather_data(station_id, start_date, end_date, city_name):
    """Fetch weather data from NOAA API with improved error handling."""
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    
    params = {
        'datasetid': 'GHCND',
        'stationid': station_id,
        'startdate': start_date,
        'enddate': end_date,
        'datatypeid': 'TMAX,TMIN,PRCP',
        'units': 'standard',
        'limit': 1000
    }
    headers = {'token': NOAA_API_KEY}

    try:
        logging.info(f"Fetching weather data for {city_name} (station: {station_id}) from {start_date} to {end_date}")
        
        # Add rate limiting
        time.sleep(1)
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        logging.info(f"Weather API response status: {response.status_code}")

        if response.status_code == 429:
            logging.warning("Rate limit exceeded, waiting 60 seconds...")
            time.sleep(60)
            response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code != 200:
            logging.error(f"Weather API error for {station_id}: {response.status_code} - {response.text}")
            return pd.DataFrame()

        data = response.json()

        # Save raw JSON
        city_folder = Path(f"data/raw/{city_name}")
        json_file = city_folder / f"weather_{station_id}_{start_date}_{end_date}.json"
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)

        if 'results' not in data or not data['results']:
            logging.warning(f"No results in weather API response for {station_id}")
            return pd.DataFrame()

        df = pd.DataFrame(data['results'])
        if df.empty:
            logging.warning(f"Empty DataFrame for {station_id}")
            return df

        # Validate required columns
        required_cols = ['date', 'datatype', 'value']
        if not all(col in df.columns for col in required_cols):
            logging.error(f"Missing required columns in weather data for {station_id}")
            return pd.DataFrame()

        # Process data
        df_pivot = df.pivot_table(
            index='date', 
            columns='datatype', 
            values='value', 
            aggfunc='first'
        ).reset_index()
        
        # Rename columns with fallback for missing data types
        column_mapping = {'TMAX': 'temp_max_F', 'TMIN': 'temp_min_F', 'PRCP': 'precipitation'}
        df_pivot = df_pivot.rename(columns=column_mapping)
        
        # Ensure all expected columns exist
        for col in ['temp_max_F', 'temp_min_F', 'precipitation']:
            if col not in df_pivot.columns:
                df_pivot[col] = None

        df_pivot['date'] = pd.to_datetime(df_pivot['date'], errors='coerce')
        df_pivot['city'] = city_name.strip().title()
        df_pivot = df_pivot.drop_duplicates(subset=['date', 'city'])
        df_pivot = df_pivot.dropna(subset=['date'])  # Remove rows with invalid dates

        logging.info(f"Successfully processed weather data for {city_name}. Shape: {df_pivot.shape}")
        return df_pivot

    except requests.RequestException as e:
        logging.error(f"Network error fetching weather data for {city_name}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching weather data for {city_name}: {e}")

    return pd.DataFrame()

def fetch_energy_data(region_code, start_date, end_date, city_name):
    """Fetch energy data from EIA API with improved error handling."""
    endpoints = [
        "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/",
        "https://api.eia.gov/v2/electricity/state-electricity-profiles/net-generation-by-state/data/",
        "https://api.eia.gov/v2/electricity/operating-generator-capacity/data/"
    ]

    for i, endpoint in enumerate(endpoints):
        try:
            logging.info(f"Trying EIA endpoint {i+1}/{len(endpoints)}: {endpoint}")
            
            # Add rate limiting
            time.sleep(1)
            
            params = {
                'api_key': EIA_API_KEY,
                'frequency': 'daily',
                'start': start_date,
                'end': end_date,
                'data[0]': 'value',
                'sort[0][column]': 'period',
                'sort[0][direction]': 'desc'
            }

            if 'rto' in endpoint:
                params['facets[respondent][]'] = region_code
            elif 'state' in endpoint:
                params['facets[stateId][]'] = region_code

            response = requests.get(endpoint, params=params, timeout=30)
            logging.info(f"EIA API response status: {response.status_code}")

            if response.status_code == 429:
                logging.warning("Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                response = requests.get(endpoint, params=params, timeout=30)

            if response.status_code != 200:
                logging.warning(f"EIA API error for {endpoint}: {response.status_code} - {response.text}")
                continue

            data = response.json()

            # Save raw JSON
            city_folder = Path(f"data/raw/{city_name}")
            json_file = city_folder / f"energy_{region_code}_{start_date}_{end_date}_endpoint{i+1}.json"
            with open(json_file, "w") as f:
                json.dump(data, f, indent=2)

            if 'response' not in data or 'data' not in data['response']:
                logging.warning(f"No data records in response for {region_code} at {endpoint}")
                continue

            records = data['response']['data']
            if not records:
                logging.warning(f"No records found for {region_code} at {endpoint}")
                continue

            df = pd.DataFrame(records)
            df['city'] = city_name.strip().title()
            
            # Standardize date column name to match weather data
            if 'period' in df.columns:
                df['date'] = pd.to_datetime(df['period'], errors='coerce')
                df = df.drop('period', axis=1)
            
            df = df.dropna(subset=['date'])
            df = df.drop_duplicates(subset=['city', 'date'])
            
            # Rename value column to be more descriptive
            if 'value' in df.columns:
                df = df.rename(columns={'value': 'energy_demand_MW'})

            logging.info(f"Energy data fetched successfully for {city_name}. Shape: {df.shape}")
            return df

        except requests.RequestException as e:
            logging.error(f"Network error with {endpoint}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error with {endpoint}: {e}")

    logging.error(f"Failed to fetch energy data from all endpoints for {region_code}")
    return pd.DataFrame()

def combine_weather_backups(start_date, end_date):
    """Combine weather data across cities into backup file."""
    combined = []

    for city in config['cities']:
        city_name = city['name']
        # Fix: Use correct file path pattern
        csv_pattern = f"weather_{city_name}_{start_date}_{end_date}.csv"
        path = Path(f"data/raw/{city_name}") / csv_pattern
        
        if path.exists():
            try:
                df = pd.read_csv(path)
                df['city'] = city_name
                combined.append(df)
                logging.info(f"Added {city_name} weather data to backup ({len(df)} rows)")
            except Exception as e:
                logging.error(f"Error reading weather data for {city_name}: {e}")

    if combined:
        full_df = pd.concat(combined, ignore_index=True)
        backup_path = Path("data/backup/backup_weather.csv")
        full_df.to_csv(backup_path, index=False)
        logging.info(f"Combined backup_weather.csv saved with {len(full_df)} total rows.")
        return True
    else:
        logging.warning("No weather data to combine.")
        return False

def combine_energy_backups(start_date, end_date):
    """Combine energy data across cities into backup file."""
    combined = []

    for city in config['cities']:
        city_name = city['name']
        # Fix: Use correct file path pattern
        csv_pattern = f"energy_{city_name}_{start_date}_{end_date}.csv"
        path = Path(f"data/raw/{city_name}") / csv_pattern
        
        if path.exists():
            try:
                df = pd.read_csv(path)
                df['city'] = city_name
                combined.append(df)
                logging.info(f"Added {city_name} energy data to backup ({len(df)} rows)")
            except Exception as e:
                logging.error(f"Error reading energy data for {city_name}: {e}")

    if combined:
        full_df = pd.concat(combined, ignore_index=True)
        backup_path = Path("data/backup/backup_energy.csv")
        full_df.to_csv(backup_path, index=False)
        logging.info(f"Combined backup_energy.csv saved with {len(full_df)} total rows.")
        return True
    else:
        logging.warning(" No energy data to combine.")
        return False

def main():
    """Main function to orchestrate data fetching."""
    try:
        # Create necessary directories
        create_directories()
        
        # Calculate date range (consider making this configurable)
        start_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")  # Reduced from 90 days
        end_date = datetime.today().strftime("%Y-%m-%d")
        
        logging.info(f"Starting data fetch for period: {start_date} to {end_date}")
        
        success_count = {'weather': 0, 'energy': 0}
        total_cities = len(config['cities'])

        for i, city in enumerate(config['cities'], 1):
            city_name = city['name']
            logging.info(f"Processing city {i}/{total_cities}: {city_name}")

            # Fetch weather data
            try:
                weather_df = fetch_weather_data(city['station_id'], start_date, end_date, city_name)
                if not weather_df.empty:
                    csv_path = Path(f"data/raw/{city_name}/weather_{city_name}_{start_date}_{end_date}.csv")
                    weather_df.to_csv(csv_path, index=False)
                    logging.info(f"Saved weather data for {city_name} ({len(weather_df)} rows)")
                    success_count['weather'] += 1
                else:
                    logging.warning(f"No weather data retrieved for {city_name}")
            except Exception as e:
                logging.error(f"Failed to process weather data for {city_name}: {e}")

            # Fetch energy data
            try:
                energy_df = fetch_energy_data(city['region_code'], start_date, end_date, city_name)
                if not energy_df.empty:
                    csv_path = Path(f"data/raw/{city_name}/energy_{city_name}_{start_date}_{end_date}.csv")
                    energy_df.to_csv(csv_path, index=False)
                    logging.info(f"Saved energy data for {city_name} ({len(energy_df)} rows)")
                    success_count['energy'] += 1
                else:
                    logging.warning(f"No energy data retrieved for {city_name}")
            except Exception as e:
                logging.error(f"Failed to process energy data for {city_name}: {e}")

            # Add delay between cities to respect rate limits
            if i < total_cities:
                time.sleep(2)

        # Generate summary
        logging.info(f"Data fetch completed: {success_count['weather']}/{total_cities} weather, {success_count['energy']}/{total_cities} energy")

        # Combine data into backups
        weather_backup_success = combine_weather_backups(start_date, end_date)
        energy_backup_success = combine_energy_backups(start_date, end_date)
        
        if weather_backup_success and energy_backup_success:
            logging.info("All data processing completed successfully!")
        else:
            logging.warning("Some backup files could not be created")

    except Exception as e:
        logging.error(f"Fatal error in main function: {e}")
        raise

if __name__ == "__main__":
    main()