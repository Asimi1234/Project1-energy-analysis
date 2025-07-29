import pandas as pd
import pytest
import sys
import os
from datetime import datetime, timezone, timedelta

# Add src to path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.analysis import check_missing_values, detect_outliers, check_data_freshness, generate_quality_report


@pytest.fixture
def sample_clean_df():
    """Fixture for a sample clean, merged DataFrame."""
    # Use timezone-aware datetime for consistency
    recent_date = datetime.now(timezone.utc) - timedelta(days=1)
    data = {
        "date": pd.to_datetime([
            "2024-05-01", 
            "2024-05-02", 
            recent_date
        ], utc=True),
        "temp_max_F": [70, 135, 65],  # 135 is an outlier (>130)
        "temp_min_F": [50, 55, -60],  # -60 is an outlier (<-50)
        "energy_demand_MW": [20000, 25000, -100],  # -100 is negative
        "city": ["New York", "New York", "Chicago"]
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_with_missing_values():
    """Fixture for DataFrame with missing values."""
    data = {
        "a": [1, None, 3],
        "b": [2, 3, None],
        "c": [None, None, None]
    }
    return pd.DataFrame(data)


@pytest.fixture
def empty_df():
    """Fixture for empty DataFrame."""
    return pd.DataFrame(columns=["date", "temp_max_F", "energy_demand_MW"])


@pytest.fixture
def df_with_invalid_dates():
    """Fixture for DataFrame with invalid dates."""
    data = {
        "date": ["2024-05-01", "invalid_date", None],
        "temp_max_F": [70, 80, 75],
        "energy_demand_MW": [1000, 2000, 1500]
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_non_numeric_columns():
    """Fixture for DataFrame with non-numeric temperature columns."""
    data = {
        "date": pd.to_datetime(["2024-05-01", "2024-05-02"]),
        "temp_max_F": ["hot", "cold"],  # Non-numeric
        "energy_demand_MW": [1000, 2000]
    }
    return pd.DataFrame(data)


def test_check_missing_values(df_with_missing_values):
    """Test missing values detection."""
    missing = check_missing_values(df_with_missing_values)
    assert missing["a"] == 1
    assert missing["b"] == 1
    assert missing["c"] == 3


def test_check_missing_values_empty_df(empty_df):
    """Test missing values with empty DataFrame."""
    missing = check_missing_values(empty_df)
    assert all(count == 0 for count in missing)


def test_check_missing_values_type_error():
    """Test that TypeError is raised for non-DataFrame input."""
    with pytest.raises(TypeError, match="Input must be a pandas DataFrame"):
        check_missing_values([1, 2, 3])


def test_detect_outliers(sample_clean_df):
    """Test outlier detection with valid data."""
    outliers = detect_outliers(sample_clean_df, ["temp_max_F", "temp_min_F"], "energy_demand_MW")
    assert outliers["temp_max_F"] == 1  # 135 > 130
    assert outliers["temp_min_F"] == 1  # -60 < -50
    assert outliers["energy_demand_MW"] == 1  # -100 < 0


def test_detect_outliers_missing_columns():
    """Test outlier detection with missing columns."""
    df = pd.DataFrame({"existing_col": [1, 2, 3]})
    outliers = detect_outliers(df, ["missing_temp"], "missing_energy")
    assert outliers["missing_temp"] == "Column not found"
    assert outliers["missing_energy"] == "Column not found"


def test_detect_outliers_non_numeric(df_non_numeric_columns):
    """Test outlier detection with non-numeric columns."""
    outliers = detect_outliers(df_non_numeric_columns, ["temp_max_F"], "energy_demand_MW")
    assert "not numeric" in outliers["temp_max_F"]
    assert outliers["energy_demand_MW"] == 0  # No negative values


def test_detect_outliers_type_error():
    """Test that TypeError is raised for non-DataFrame input."""
    with pytest.raises(TypeError, match="Input must be a pandas DataFrame"):
        detect_outliers("not_a_dataframe", ["temp"], "energy")


def test_check_data_freshness_fresh(sample_clean_df):
    """Test freshness check with recent data."""
    freshness = check_data_freshness(sample_clean_df, "date")
    assert freshness["is_fresh"] is True
    assert freshness["days_ago"] <= 2
    assert "latest_date" in freshness
    assert "total_records" in freshness
    assert "valid_dates" in freshness


def test_check_data_freshness_stale():
    """Test freshness check with old data."""
    old_data = {
        "date": pd.to_datetime(["2024-01-01", "2024-01-02"], utc=True),
        "value": [1, 2]
    }
    df = pd.DataFrame(old_data)
    freshness = check_data_freshness(df, "date")
    assert freshness["is_fresh"] is False
    assert freshness["days_ago"] > 2


def test_check_data_freshness_missing_column():
    """Test freshness check with missing date column."""
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    with pytest.raises(ValueError, match="missing_date column not found"):
        check_data_freshness(df, "missing_date")


def test_check_data_freshness_empty_df(empty_df):
    """Test freshness check with empty DataFrame."""
    freshness = check_data_freshness(empty_df, "date")
    assert freshness["is_fresh"] is False
    assert freshness["latest_date"] is None
    assert "error" in freshness


def test_check_data_freshness_invalid_dates(df_with_invalid_dates):
    """Test freshness check with invalid dates."""
    freshness = check_data_freshness(df_with_invalid_dates, "date")
    # Should handle invalid dates gracefully
    assert "error" in freshness or freshness["valid_dates"] < len(df_with_invalid_dates)


def test_check_data_freshness_type_error():
    """Test that TypeError is raised for non-DataFrame input."""
    with pytest.raises(TypeError, match="Input must be a pandas DataFrame"):
        check_data_freshness("not_a_dataframe", "date")


def test_generate_quality_report(sample_clean_df):
    """Test the main report generation function."""
    report = generate_quality_report(
        sample_clean_df, 
        ["temp_max_F", "temp_min_F"], 
        "energy_demand_MW", 
        "date"
    )
    
    # Check all main sections exist
    assert "dataset_info" in report
    assert "missing_values" in report
    assert "outliers" in report
    assert "freshness" in report
    
    # Check dataset info
    assert report["dataset_info"]["total_rows"] == 3
    assert report["dataset_info"]["total_columns"] == 5  # date, temp_max_F, temp_min_F, energy_demand_MW, city
    assert "columns" in report["dataset_info"]
    
    # Check specific values
    assert report["outliers"]["temp_max_F"] == 1
    assert report["outliers"]["temp_min_F"] == 1
    assert report["outliers"]["energy_demand_MW"] == 1
    assert report["freshness"]["is_fresh"] is True


def test_generate_quality_report_type_errors():
    """Test type validation in generate_quality_report."""
    df = pd.DataFrame({"col": [1, 2, 3]})
    
    # Test non-DataFrame input
    with pytest.raises(TypeError, match="Input must be a pandas DataFrame"):
        generate_quality_report("not_df", ["temp"], "energy", "date")
    
    # Test non-list temp_cols
    with pytest.raises(TypeError, match="temp_cols must be a list or tuple"):
        generate_quality_report(df, "not_list", "energy", "date")
    
    # Test non-string energy_col
    with pytest.raises(TypeError, match="energy_col must be a string"):
        generate_quality_report(df, ["temp"], 123, "date")
    
    # Test non-string date_col
    with pytest.raises(TypeError, match="date_col must be a string"):
        generate_quality_report(df, ["temp"], "energy", 123)


def test_generate_quality_report_with_errors():
    """Test report generation handles errors gracefully."""
    # DataFrame with problematic data
    df = pd.DataFrame({"date": ["invalid"], "temp": ["not_numeric"]})
    
    report = generate_quality_report(df, ["temp"], "missing_energy", "date")
    
    # Should not crash and should contain error information
    assert isinstance(report, dict)
    # Either the report succeeds partially or contains error info
    assert "missing_values" in report or "error" in report


def test_integration_with_mixed_data():
    """Integration test with mixed quality data."""
    data = {
        "date": pd.to_datetime([
            "2024-05-01", 
            datetime.now(timezone.utc) - timedelta(hours=12)
        ], utc=True),
        "temp1": [25, None],  # Missing value
        "temp2": [200, 30],   # Outlier
        "energy": [1000, -50], # Negative energy
        "other": ["a", "b"]   # Non-numeric
    }
    df = pd.DataFrame(data)
    
    report = generate_quality_report(df, ["temp1", "temp2"], "energy", "date")
    
    assert report["missing_values"]["temp1"] == 1
    assert report["outliers"]["temp1"] == 0  # Can't check outliers on missing data
    assert report["outliers"]["temp2"] == 1  # 200 > 130
    assert report["outliers"]["energy"] == 1  # -50 < 0
    assert report["freshness"]["is_fresh"] is True