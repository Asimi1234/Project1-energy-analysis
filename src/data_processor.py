import pandas as pd
import logging


def process_energy_data(df):
    """
    Process energy data into a clean DataFrame with standardized 'date' and 'energy_demand_MW' columns.
    Includes defensive checks, flexible column detection, and detailed logging.
    """
    logging.info(f"Energy DataFrame shape: {df.shape}")
    logging.info(f"Energy DataFrame columns: {df.columns.tolist()}")

    if df.empty:
        logging.warning("Received empty DataFrame for energy data.")
        return pd.DataFrame(columns=["date", "energy_demand_MW"])

    logging.info(f"First 3 rows of energy data:\n{df.head(3)}")
    logging.info(f"Data types:\n{df.dtypes}")

    possible_demand_columns = [
        'demand', 'Demand', 'DEMAND',
        'demand_mw', 'demand_MW', 'Demand_MW',
        'load', 'Load', 'LOAD',
        'consumption', 'Consumption', 'CONSUMPTION',
        'value', 'Value', 'VALUE'
    ]

    demand_column = next((col for col in possible_demand_columns if col in df.columns), None)
    if demand_column:
        logging.info(f"Found demand column: {demand_column}")
    else:
        logging.error(f"No demand column found. Available columns: {df.columns.tolist()}")
        return pd.DataFrame(columns=["date", "energy_demand_MW"])

    possible_date_columns = [
        'date', 'Date', 'DATE',
        'period', 'Period', 'PERIOD',
        'timestamp', 'Timestamp', 'TIMESTAMP',
        'time', 'Time', 'TIME'
    ]

    date_column = next((col for col in possible_date_columns if col in df.columns), None)
    if date_column:
        logging.info(f"Found date column: {date_column}")
    else:
        logging.error(f"No date column found. Available columns: {df.columns.tolist()}")
        return pd.DataFrame(columns=["date", "energy_demand_MW"])

    try:
        df_clean = df[[date_column, demand_column]].copy()
        df_clean = df_clean.rename(columns={date_column: "date", demand_column: "energy_demand_MW"})

        df_clean["date"] = pd.to_datetime(df_clean["date"], errors='coerce')
        df_clean["energy_demand_MW"] = pd.to_numeric(df_clean["energy_demand_MW"], errors='coerce')

        df_clean = df_clean.dropna(subset=["date", "energy_demand_MW"])

        logging.info(f"Processed energy data shape: {df_clean.shape}")
        return df_clean

    except Exception as e:
        logging.error(f"Error processing energy data: {e}")
        return pd.DataFrame(columns=["date", "energy_demand_MW"])


def process_weather_data(df):
    """
    Process weather data into a clean DataFrame with standardized 'date', 'temp_max_F', 'temp_min_F' columns.
    Includes defensive checks and detailed logging.
    """
    logging.info(f"Weather DataFrame shape: {df.shape}")
    logging.info(f"Weather DataFrame columns: {df.columns.tolist()}")

    if df.empty:
        logging.warning("Received empty DataFrame for weather data.")
        return pd.DataFrame(columns=["date", "temp_max_F", "temp_min_F"])

    logging.info(f"First 3 rows of weather data:\n{df.head(3)}")

    required_columns = ['date', 'temp_max_F', 'temp_min_F']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        logging.error(f"Missing weather columns: {missing_columns}")
        logging.error(f"Available columns: {df.columns.tolist()}")
        return pd.DataFrame(columns=["date", "temp_max_F", "temp_min_F"])

    try:
        df_clean = df[required_columns].copy()

        df_clean["date"] = pd.to_datetime(df_clean["date"], errors='coerce')
        df_clean["temp_max_F"] = pd.to_numeric(df_clean["temp_max_F"], errors='coerce')
        df_clean["temp_min_F"] = pd.to_numeric(df_clean["temp_min_F"], errors='coerce')

        df_clean = df_clean.dropna(subset=["date", "temp_max_F", "temp_min_F"])

        logging.info(f"Processed weather data shape: {df_clean.shape}")
        return df_clean

    except Exception as e:
        logging.error(f"Error processing weather data: {e}")
        return pd.DataFrame(columns=["date", "temp_max_F", "temp_min_F"])
