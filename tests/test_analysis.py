import pandas as pd
import pytest
import sys
import os

# Add src to path to allow for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.analysis import check_missing_values, detect_outliers, check_data_freshness, generate_quality_report

@pytest.fixture
def sample_clean_df():
    """Fixture for a sample clean, merged DataFrame."""
    data = {
        "date": pd.to_datetime(["2024-05-01", "2024-05-02", pd.Timestamp.now().normalize()]),
        "temp_max_F": [70, 135, 65],
        "temp_min_F": [50, 55, -60],
        "energy_demand_MW": [20000, 25000, -100],
        "city": ["New York", "New York", "Chicago"]
    }
    return pd.DataFrame(data)

def test_check_missing_values():
    df = pd.DataFrame({"a": [1, None], "b": [2, 3]})
    missing = check_missing_values(df)
    assert missing["a"] == 1
    assert missing["b"] == 0

def test_detect_outliers(sample_clean_df):
    outliers = detect_outliers(sample_clean_df, ["temp_max_F", "temp_min_F"], "energy_demand_MW")
    assert outliers["temp_max_F"] == 1
    assert outliers["temp_min_F"] == 1
    assert outliers["energy_demand_MW"] == 1

def test_check_data_freshness(sample_clean_df):
    freshness = check_data_freshness(sample_clean_df, "date")
    assert freshness["is_fresh"] is True

def test_generate_quality_report(sample_clean_df):
    """Test the main report generation function."""
    report = generate_quality_report(sample_clean_df, ["temp_max_F", "temp_min_F"], "energy_demand_MW", "date")
    
    assert "missing_values" in report
    assert "outliers" in report
    assert "freshness" in report
    assert report["outliers"]["temp_max_F"] == 1
    assert report["freshness"]["is_fresh"] is True