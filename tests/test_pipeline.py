import pytest
import pandas as pd
from src.data_fetcher import fetch_weather_data, fetch_energy_data
from src.data_processor import process_weather_data, process_energy_data
from src.analysis import check_missing_values, detect_outliers, check_data_freshness

def test_fetch_weather_data():
    df = fetch_weather_data("GHCND:USW00094728", "2024-01-01", "2024-01-02")
    assert isinstance(df, pd.DataFrame)

def test_fetch_energy_data():
    df = fetch_energy_data("NYIS", "2024-01-01", "2024-01-02")
    assert isinstance(df, pd.DataFrame)

def test_process_weather_data_empty():
    df = process_weather_data(pd.DataFrame())
    assert df.empty

def test_process_energy_data_empty():
    df = process_energy_data(pd.DataFrame())
    assert df.empty

def test_check_missing_values():
    df = pd.DataFrame({"a": [1, None], "b": [2, 3]})
    missing = check_missing_values(df)
    assert missing["a"] == 1
    assert missing["b"] == 0

def test_detect_outliers():
    data = {
        "temp_max_F": [60, 135, -60],
        "temp_min_F": [40, 50, -70],
        "energy_demand_MW": [5000, -300, 4000]
    }
    df = pd.DataFrame(data)
    outliers = detect_outliers(df, ["temp_max_F", "temp_min_F"], "energy_demand_MW")
    assert outliers["temp_max_F"] == 2
    assert outliers["temp_min_F"] == 1
    assert outliers["energy_demand_MW"] == 1

def test_check_data_freshness():
    today = pd.Timestamp.today().normalize()
    df = pd.DataFrame({"date": [today]})
    freshness = check_data_freshness(df, "date")
    assert freshness["is_fresh"] is True
