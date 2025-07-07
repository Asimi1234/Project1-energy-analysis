import requests
import pandas as pd
import logging
import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load config
CONFIG_PATH = Path("config/config.yaml")

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

config = load_config()

# Load API keys from environment variables
NOAA_API_KEY = os.getenv("NOAA_API_KEY")
EIA_API_KEY = os.getenv("EIA_API_KEY")

if not NOAA_API_KEY or not EIA_API_KEY:
    raise ValueError("API keys not found in .env file")

# Fetch weather data
def fetch_weather_data(station_id, start_date, end_date):
    url = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
    params = [
    ('datasetid', 'GHCND'),
    ('stationid', station_id),
    ('startdate', start_date),
    ('enddate', end_date),
    ('datatypeid', 'TMAX'),
    ('datatypeid', 'TMIN'),
    ('datatypeid', 'PRCP'),
    ('units', 'standard'),
    ('limit', 1000)
    ]
    headers = {'token': NOAA_API_KEY}

    try:
        logging.info(f"Fetching weather data for {station_id} from {start_date} to {end_date}")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        logging.info(f"Weather API response status: {response.status_code}")

        if response.status_code != 200:
            logging.error(f"Weather API error for {station_id}: {response.status_code} - {response.text}")
            return pd.DataFrame()

        data = response.json()

        os.makedirs("data/raw", exist_ok=True)
        with open(f"data/raw/weather_{station_id}_{start_date}_{end_date}.json", "w") as f:
            json.dump(data, f)

        if 'results' not in data:
            logging.warning(f"No results in weather API response for {station_id}")
            return pd.DataFrame()

        df = pd.DataFrame(data['results'])
        if df.empty:
            logging.warning(f"Empty DataFrame for {station_id}")
            return df

        df_pivot = df.pivot_table(index='date', columns='datatype', values='value', aggfunc='first').reset_index()
        df_pivot.rename(columns={'TMAX': 'temp_max_F', 'TMIN': 'temp_min_F', 'PRCP': 'precipitation'}, inplace=True)

        return df_pivot

    except requests.RequestException as e:
        logging.error(f"Network error fetching weather data: {e}")
    except Exception as e:
        logging.error(f"Error fetching weather data: {e}")

    return pd.DataFrame()

# Fetch energy data
def fetch_energy_data(region_code, start_date, end_date):
    endpoints = [
        "https://api.eia.gov/v2/electricity/rto/daily-region-data/data/",
        "https://api.eia.gov/v2/electricity/state-electricity-profiles/net-generation-by-state/data/",
        "https://api.eia.gov/v2/electricity/operating-generator-capacity/data/"
    ]

    for endpoint in endpoints:
        try:
            logging.info(f"Trying EIA endpoint: {endpoint}")
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

            if response.status_code != 200:
                logging.warning(f"EIA API error for {endpoint}: {response.status_code} - {response.text}")
                continue

            data = response.json()

            os.makedirs("data/raw", exist_ok=True)
            with open(f"data/raw/energy_{region_code}_{start_date}_{end_date}.json", "w") as f:
                json.dump(data, f)

            if 'response' not in data or 'data' not in data['response']:
                logging.warning(f"No data records in response for {region_code} at {endpoint}")
                continue

            records = data['response']['data']
            if not records:
                logging.warning(f"No records found for {region_code}")
                continue

            df = pd.DataFrame(records)
            logging.info(f"Energy data fetched successfully. Shape: {df.shape}")
            return df

        except requests.RequestException as e:
            logging.error(f"Network error with {endpoint}: {e}")
        except Exception as e:
            logging.error(f"Error with {endpoint}: {e}")

    return pd.DataFrame()

# Fetch for each city in config
def main():
    start_date = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")
    end_date = datetime.today().strftime("%Y-%m-%d")

    for city in config['cities']:
        city_name = city['name']
        logging.info(f"Fetching data for {city_name}")

        weather_df = fetch_weather_data(city['station_id'], start_date, end_date)
        if not weather_df.empty:
            weather_df.to_csv(f"data/raw/weather_{city_name}_{start_date}_{end_date}.csv", index=False)
            logging.info(f"Saved weather data for {city_name}")

        energy_df = fetch_energy_data(city['region_code'], start_date, end_date)
        if not energy_df.empty:
            energy_df.to_csv(f"data/raw/energy_{city_name}_{start_date}_{end_date}.csv", index=False)
            logging.info(f"Saved energy data for {city_name}")
        else:
            logging.error(f"Failed to fetch energy data for {city['region_code']}")

if __name__ == "__main__":
    main()
