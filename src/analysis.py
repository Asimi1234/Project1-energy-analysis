import pandas as pd
import numpy as np


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
    for col in temp_cols:
        if col in df.columns:
            outliers[col] = df[(df[col] > 130) | (df[col] < -50)].shape[0]
        else:
            outliers[col] = 'Column not found'
    if energy_col in df.columns:
        outliers[energy_col] = df[df[energy_col] < 0].shape[0]
    else:
        outliers[energy_col] = 'Column not found'
    return outliers


def check_data_freshness(df, date_col):
    """Check if the latest data is within 2 days of today."""
    if date_col not in df.columns:
        raise ValueError(f"{date_col} column not found in DataFrame")

    latest_date = df[date_col].max()
    if pd.isnull(latest_date):
        return {"latest_date": None, "days_ago": None, "is_fresh": False}

    if latest_date.tzinfo is None:
        latest_date = latest_date.tz_localize('UTC')

    days_diff = (pd.Timestamp.now(tz='UTC') - latest_date).days
    is_fresh = days_diff <= 2

    return {"latest_date": latest_date, "days_ago": days_diff, "is_fresh": is_fresh}


def generate_quality_report(df, temp_cols, energy_col, date_col):
    """Compile a full data quality report."""
    report = {
        "missing_values": check_missing_values(df).to_dict(),
        "outliers": detect_outliers(df, temp_cols, energy_col),
        "freshness": check_data_freshness(df, date_col)
    }
    return report
