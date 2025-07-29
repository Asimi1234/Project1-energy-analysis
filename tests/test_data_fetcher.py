import pytest
import pandas as pd
import sys
import os
from unittest.mock import Mock, patch, mock_open
import json
from pathlib import Path

# Add src to path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.data_fetcher import (
    fetch_weather_data, 
    fetch_energy_data, 
    combine_weather_backups, 
    combine_energy_backups,
    create_directories,
    load_config
)


@pytest.fixture
def mock_config():
    """Mock configuration data."""
    return {
        'cities': [
            {
                'name': 'New York',
                'station_id': 'GHCND:USW00094728',
                'region_code': 'NYC'
            },
            {
                'name': 'Chicago',
                'station_id': 'GHCND:USW00094846',
                'region_code': 'MISO'
            }
        ]
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv('NOAA_API_KEY', 'fake_noaa_key')
    monkeypatch.setenv('EIA_API_KEY', 'fake_eia_key')


class TestWeatherDataFetching:
    """Test suite for weather data fetching functionality."""

    def test_fetch_weather_data_success(self, mocker, mock_env_vars):
        """Test successful weather data fetching by mocking the API call."""
        # Arrange: Create a fake JSON response
        mock_response_data = {
            "results": [
                {"date": "2024-01-01T00:00:00", "datatype": "TMAX", "value": 35.1},
                {"date": "2024-01-01T00:00:00", "datatype": "TMIN", "value": 25.2},
                {"date": "2024-01-02T00:00:00", "datatype": "TMAX", "value": 40.0},
                {"date": "2024-01-02T00:00:00", "datatype": "TMIN", "value": 30.0}
            ]
        }
        
        # Mock the API response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mocker.patch('requests.get', return_value=mock_response)
        
        # Mock file operations and directory creation
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('builtins.open', mock_open())
        mocker.patch('json.dump')
        mocker.patch('time.sleep')  # Skip rate limiting in tests

        # Act: Call the function
        df = fetch_weather_data("FAKE_STATION", "2024-01-01", "2024-01-02", "Test City")

        # Assert: Check that the output is a correctly structured DataFrame
        assert not df.empty
        assert 'temp_max_F' in df.columns
        assert 'temp_min_F' in df.columns
        assert 'city' in df.columns
        assert 'date' in df.columns
        assert df.shape[0] == 2  # Two days of data
        assert df['temp_max_F'].iloc[0] == 35.1
        assert df['temp_min_F'].iloc[0] == 25.2
        assert df['city'].iloc[0] == 'Test City'

    def test_fetch_weather_data_api_error(self, mocker, mock_env_vars):
        """Test that an empty DataFrame is returned on API error."""
        # Arrange: Configure the mock to simulate an API error
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mocker.patch('requests.get', return_value=mock_response)
        mocker.patch('time.sleep')  # Skip rate limiting in tests

        # Act: Call the function
        df = fetch_weather_data("FAKE_STATION", "2024-01-01", "2024-01-02", "Test City")

        # Assert: Ensure the function handled the error gracefully
        assert df.empty

    def test_fetch_weather_data_rate_limit_retry(self, mocker, mock_env_vars):
        """Test that the function handles rate limiting and retries."""
        # Arrange: First response is rate limited, second is successful
        mock_response_429 = mocker.Mock()
        mock_response_429.status_code = 429
        
        mock_response_200 = mocker.Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "results": [
                {"date": "2024-01-01T00:00:00", "datatype": "TMAX", "value": 35.1}
            ]
        }
        
        mocker.patch('requests.get', side_effect=[mock_response_429, mock_response_200])
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('builtins.open', mock_open())
        mocker.patch('json.dump')
        mock_sleep = mocker.patch('time.sleep')

        # Act
        df = fetch_weather_data("FAKE_STATION", "2024-01-01", "2024-01-02", "Test City")

        # Assert: Check that retry logic worked
        assert not df.empty
        assert mock_sleep.call_count >= 2  # Initial delay + rate limit delay

    def test_fetch_weather_data_no_results(self, mocker, mock_env_vars):
        """Test handling of API response with no results."""
        # Arrange: Response with no results
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metadata": {}}  # No 'results' key
        mocker.patch('requests.get', return_value=mock_response)
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('builtins.open', mock_open())
        mocker.patch('json.dump')
        mocker.patch('time.sleep')

        # Act
        df = fetch_weather_data("FAKE_STATION", "2024-01-01", "2024-01-02", "Test City")

        # Assert
        assert df.empty

    def test_fetch_weather_data_missing_columns(self, mocker, mock_env_vars):
        """Test handling of malformed API response missing required columns."""
        # Arrange: Response missing required columns
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"invalid_column": "value"}  # Missing date, datatype, value
            ]
        }
        mocker.patch('requests.get', return_value=mock_response)
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('builtins.open', mock_open())
        mocker.patch('json.dump')
        mocker.patch('time.sleep')

        # Act
        df = fetch_weather_data("FAKE_STATION", "2024-01-01", "2024-01-02", "Test City")

        # Assert
        assert df.empty


class TestEnergyDataFetching:
    """Test suite for energy data fetching functionality."""

    def test_fetch_energy_data_success_first_endpoint(self, mocker, mock_env_vars):
        """Test successful energy data fetching from first endpoint."""
        # Arrange: Mock successful response from RTO endpoint
        mock_response_data = {
            "response": {
                "data": [
                    {"period": "2024-01-01T00:00:00", "value": 25000, "respondent": "NYC"},
                    {"period": "2024-01-02T00:00:00", "value": 26000, "respondent": "NYC"}
                ]
            }
        }
        
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mocker.patch('requests.get', return_value=mock_response)
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('builtins.open', mock_open())
        mocker.patch('json.dump')
        mocker.patch('time.sleep')

        # Act
        df = fetch_energy_data("NYC", "2024-01-01", "2024-01-02", "New York")

        # Assert
        assert not df.empty
        assert 'date' in df.columns  # Should be renamed from 'period'
        assert 'energy_demand_MW' in df.columns  # Should be renamed from 'value'
        assert 'city' in df.columns
        assert df.shape[0] == 2
        assert df['energy_demand_MW'].iloc[0] == 25000
        assert df['city'].iloc[0] == 'New York'

    def test_fetch_energy_data_fallback_to_second_endpoint(self, mocker, mock_env_vars):
        """Test fallback to second endpoint when first fails."""
        # Arrange: First endpoint fails, second succeeds
        mock_response_fail = mocker.Mock()
        mock_response_fail.status_code = 404
        
        mock_response_success = mocker.Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "response": {
                "data": [
                    {"period": "2024-01-01T00:00:00", "value": 15000}
                ]
            }
        }
        
        mocker.patch('requests.get', side_effect=[mock_response_fail, mock_response_success])
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('builtins.open', mock_open())
        mocker.patch('json.dump')
        mocker.patch('time.sleep')

        # Act
        df = fetch_energy_data("TEST", "2024-01-01", "2024-01-02", "Test City")

        # Assert
        assert not df.empty
        assert df['energy_demand_MW'].iloc[0] == 15000

    def test_fetch_energy_data_all_endpoints_fail(self, mocker, mock_env_vars):
        """Test that empty DataFrame is returned when all endpoints fail."""
        # Arrange: All endpoints return errors
        mock_response = mocker.Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mocker.patch('requests.get', return_value=mock_response)
        mocker.patch('time.sleep')

        # Act
        df = fetch_energy_data("TEST", "2024-01-01", "2024-01-02", "Test City")

        # Assert
        assert df.empty


class TestDataCombination:
    """Test suite for data combination functionality."""

    def test_combine_weather_backups_success(self, mocker, mock_config):
        """Test successful combination of weather backup files."""
        # Arrange: Mock CSV files exist and have data
        sample_data1 = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'temp_max_F': [35.0, 40.0],
            'temp_min_F': [25.0, 30.0]
        })
        sample_data2 = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'temp_max_F': [32.0, 38.0],
            'temp_min_F': [22.0, 28.0]
        })
        
        # Mock Path.exists to return True for test files
        def mock_exists(self):
            return str(self).endswith('.csv')
        
        mocker.patch.object(Path, 'exists', mock_exists)
        mocker.patch('pandas.read_csv', side_effect=[sample_data1, sample_data2])
        mock_to_csv = mocker.patch.object(pd.DataFrame, 'to_csv')
        
        # Mock config
        with patch('src.data_fetcher.config', mock_config):
            # Act
            result = combine_weather_backups("2024-01-01", "2024-01-02")

        # Assert
        assert result is True
        mock_to_csv.assert_called_once()

    def test_combine_weather_backups_no_files(self, mocker, mock_config):
        """Test combination when no CSV files exist."""
        # Arrange: Mock that no files exist
        mocker.patch.object(Path, 'exists', return_value=False)
        
        with patch('src.data_fetcher.config', mock_config):
            # Act
            result = combine_weather_backups("2024-01-01", "2024-01-02")

        # Assert
        assert result is False

    def test_combine_energy_backups_success(self, mocker, mock_config):
        """Test successful combination of energy backup files."""
        # Arrange: Mock CSV files exist and have data
        sample_data1 = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'energy_demand_MW': [25000, 26000]
        })
        sample_data2 = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'energy_demand_MW': [15000, 16000]
        })
        
        def mock_exists(self):
            return str(self).endswith('.csv')
        
        mocker.patch.object(Path, 'exists', mock_exists)
        mocker.patch('pandas.read_csv', side_effect=[sample_data1, sample_data2])
        mock_to_csv = mocker.patch.object(pd.DataFrame, 'to_csv')
        
        with patch('src.data_fetcher.config', mock_config):
            # Act
            result = combine_energy_backups("2024-01-01", "2024-01-02")

        # Assert
        assert result is True
        mock_to_csv.assert_called_once()


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_create_directories(self, mocker):
        """Test directory creation functionality."""
        # Arrange
        mock_mkdir = mocker.patch.object(Path, 'mkdir')
        mock_config = {
            'cities': [
                {'name': 'New York'},
                {'name': 'Chicago'}
            ]
        }
        
        with patch('src.data_fetcher.config', mock_config):
            # Act
            create_directories()

        # Assert: Check that all necessary directories are created
        expected_calls = mock_mkdir.call_count
        assert expected_calls >= 5  # Base directories + city directories

    def test_load_config_success(self, mocker):
        """Test successful config loading."""
        # Arrange
        mock_config_data = {'cities': [{'name': 'Test City'}]}
        mock_file = mock_open(read_data=json.dumps(mock_config_data))
        
        with patch('builtins.open', mock_file):
            with patch('yaml.safe_load', return_value=mock_config_data):
                # Act
                config = load_config()

        # Assert
        assert config == mock_config_data

    def test_load_config_file_not_found(self, mocker):
        """Test config loading when file doesn't exist."""
        # Arrange
        mocker.patch('builtins.open', side_effect=FileNotFoundError)

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            load_config()


class TestIntegration:
    """Integration tests for the data fetcher module."""

    def test_weather_and_energy_data_consistency(self, mocker, mock_env_vars):
        """Test that weather and energy data have consistent date formats."""
        # Arrange: Mock responses for both APIs
        weather_response = {
            "results": [
                {"date": "2024-01-01T00:00:00", "datatype": "TMAX", "value": 35.1}
            ]
        }
        energy_response = {
            "response": {
                "data": [
                    {"period": "2024-01-01T00:00:00", "value": 25000}
                ]
            }
        }
        
        mock_weather_response = mocker.Mock()
        mock_weather_response.status_code = 200
        mock_weather_response.json.return_value = weather_response
        
        mock_energy_response = mocker.Mock()
        mock_energy_response.status_code = 200
        mock_energy_response.json.return_value = energy_response
        
        # Mock requests.get to return appropriate response based on URL
        def mock_get(url, **kwargs):
            if 'ncei.noaa.gov' in url:
                return mock_weather_response
            else:
                return mock_energy_response
        
        mocker.patch('requests.get', side_effect=mock_get)
        mocker.patch('pathlib.Path.mkdir')
        mocker.patch('builtins.open', mock_open())
        mocker.patch('json.dump')
        mocker.patch('time.sleep')

        # Act
        weather_df = fetch_weather_data("TEST", "2024-01-01", "2024-01-02", "Test City")
        energy_df = fetch_energy_data("TEST", "2024-01-01", "2024-01-02", "Test City")

        # Assert: Both DataFrames should have 'date' column with datetime type
        assert 'date' in weather_df.columns
        assert 'date' in energy_df.columns
        assert pd.api.types.is_datetime64_any_dtype(weather_df['date'])
        assert pd.api.types.is_datetime64_any_dtype(energy_df['date'])