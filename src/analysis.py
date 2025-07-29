import pandas as pd
import numpy as np
from datetime import datetime, timezone


def check_missing_values(df):
    """Return number of missing values per column."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    return df.isnull().sum()


def detect_outliers(df, temp_cols, energy_col):
    """Flag temperature outliers and negative energy values."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    
    outliers = {}
    
    # Check temperature columns
    for col in temp_cols:
        if col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                outliers[col] = df[(df[col] > 130) | (df[col] < -50)].shape[0]
            else:
                outliers[col] = f'Column {col} is not numeric'
        else:
            outliers[col] = 'Column not found'
    
    # Check energy column
    if energy_col in df.columns:
        if pd.api.types.is_numeric_dtype(df[energy_col]):
            outliers[energy_col] = df[df[energy_col] < 0].shape[0]
        else:
            outliers[energy_col] = f'Column {energy_col} is not numeric'
    else:
        outliers[energy_col] = 'Column not found'
    
    return outliers


def check_data_freshness(df, date_col):
    """Check if the latest data is within 2 days of today."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    
    if date_col not in df.columns:
        raise ValueError(f"{date_col} column not found in DataFrame")
    
    if df.empty:
        return {"latest_date": None, "days_ago": None, "is_fresh": False, "error": "DataFrame is empty"}

    try:
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            date_series = pd.to_datetime(df[date_col], errors='coerce')
        else:
            date_series = df[date_col]
        
        # Remove NaT values before finding max
        valid_dates = date_series.dropna()
        if valid_dates.empty:
            return {"latest_date": None, "days_ago": None, "is_fresh": False, "error": "No valid dates found"}
        
        latest_date = valid_dates.max()
        
        # Handle timezone-naive dates more robustly
        if latest_date.tzinfo is None:
            latest_date = latest_date.tz_localize('UTC')
        
        # Use datetime.now() with timezone for consistency
        current_time = datetime.now(timezone.utc)
        current_time_pd = pd.Timestamp(current_time)
        
        days_diff = (current_time_pd - latest_date).days
        is_fresh = days_diff <= 2

        return {
            "latest_date": latest_date.isoformat(), 
            "days_ago": days_diff, 
            "is_fresh": is_fresh,
            "total_records": len(df),
            "valid_dates": len(valid_dates)
        }
        
    except Exception as e:
        return {
            "latest_date": None, 
            "days_ago": None, 
            "is_fresh": False, 
            "error": f"Error processing dates: {str(e)}"
        }


def generate_quality_report(df, temp_cols, energy_col, date_col):
    """Compile a full data quality report."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    
    if not isinstance(temp_cols, (list, tuple)):
        raise TypeError("temp_cols must be a list or tuple")
    
    if not isinstance(energy_col, str):
        raise TypeError("energy_col must be a string")
    
    if not isinstance(date_col, str):
        raise TypeError("date_col must be a string")
    
    try:
        report = {
            "dataset_info": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": list(df.columns)
            },
            "missing_values": check_missing_values(df).to_dict(),
            "outliers": detect_outliers(df, temp_cols, energy_col),
            "freshness": check_data_freshness(df, date_col)
        }
        return report
    except Exception as e:
        return {"error": f"Error generating report: {str(e)}"}