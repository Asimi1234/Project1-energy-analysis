import pandas as pd
import pytest
import sys
import os

# Add src to path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from data_processor import process_weather_data, process_energy_data

@pytest.fixture
def sample_weather_df():
    """Fixture for sample processed weather data (already in Fahrenheit)."""
    data = {
        'date': ['2024-01-01', '2024-01-02'],
        'temp_max_F': [32.0, 35.6],
        'temp_min_F': [23.0, 28.4],
        'precipitation': [0.1, 0.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_energy_df():
    """Fixture for sample raw energy data from EIA API."""
    data = {
        'period': ['2024-01-01', '2024-01-02'],
        'respondent': ['NYIS', 'NYIS'],
        'value': [18000, 22000],
        'other_col': ['A', 'B']
    }
    return pd.DataFrame(data)

def test_process_weather_data(sample_weather_df):
    """Test weather data processing (type conversion and NaN handling)."""
    processed_df = process_weather_data(sample_weather_df)
    assert 'date' in processed_df.columns
    assert 'temp_max_F' in processed_df.columns
    assert 'temp_min_F' in processed_df.columns
    assert processed_df.shape[0] == 2
    assert pd.api.types.is_numeric_dtype(processed_df['temp_max_F'])
    assert processed_df['temp_max_F'].iloc[0] == 32.0

def test_process_energy_data(sample_energy_df):
    """Test energy data processing, column renaming, and selection."""
    processed_df = process_energy_data(sample_energy_df)
    assert list(processed_df.columns) == ['date', 'energy_demand_MW']
    assert processed_df.shape[0] == 2
    assert pd.api.types.is_datetime64_any_dtype(processed_df['date'])
    assert processed_df['energy_demand_MW'].iloc[0] == 18000