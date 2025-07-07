import pytest
import pandas as pd
import sys
import os

# Add src to path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.data_fetcher import fetch_weather_data, fetch_energy_data

def test_fetch_weather_data_success(mocker):
    """Test successful weather data fetching by mocking the API call."""
    # Arrange: Create a fake JSON response
    mock_response_data = {
        "results": [
            {"date": "2024-01-01T00:00:00", "datatype": "TMAX", "value": 35.1},
            {"date": "2024-01-01T00:00:00", "datatype": "TMIN", "value": 25.2}
        ]
    }
    # Arrange: Configure the mock to return the fake response
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mocker.patch('requests.get', return_value=mock_response)

    # Act: Call the function
    df = fetch_weather_data("FAKE_STATION", "2024-01-01", "2024-01-02")

    # Assert: Check that the output is a correctly structured DataFrame
    assert not df.empty
    assert 'temp_max_F' in df.columns
    assert df.shape[0] == 1
    assert df['temp_max_F'].iloc[0] == 35.1

def test_fetch_weather_data_api_error(mocker):
    """Test that an empty DataFrame is returned on API error."""
    # Arrange: Configure the mock to simulate an API error
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mocker.patch('requests.get', return_value=mock_response)

    # Act: Call the function
    df = fetch_weather_data("FAKE_STATION", "2024-01-01", "2024-01-02")

    # Assert: Ensure the function handled the error gracefully
    assert df.empty
