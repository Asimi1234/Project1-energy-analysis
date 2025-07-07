# Energy Demand Forecasting & Weather Analysis

A comprehensive data pipeline and analytics platform for energy demand forecasting using real-time weather data integration.

## Business Objective

Accurate energy demand forecasting is critical for minimizing costs, managing peak load, and ensuring grid stability. This project integrates real-time and historical weather data with electricity demand to support smarter forecasting and data-driven operations for utilities and grid operators.

## What This Project Delivers

### Core Features
- **Automated ETL Pipeline** - Fetches, cleans, and merges energy demand and NOAA weather data
- **Built-in Data Quality Framework** - Checks for missing values, outliers, and data freshness after each data load
- **Interactive Streamlit Dashboard** - Real-time visualization and analysis interface
- **Modular & Configurable Codebase** - Designed for easy adaptation to new cities, data sources, and formats
- **Production-Ready Structure** - Clean repo layout, config files, logging, error handling, and testability

### Dashboard Features
1. **City-level Geographic Overview** - Interactive maps and location-based insights
2. **Time Series Analysis** - Temperature vs energy demand correlation over time
3. **Correlation Analysis** - Statistical relationships between weather variables and energy consumption
4. **Usage Pattern Heatmaps** - Visual representation of consumption patterns by day/hour

### Technical Features
- **AI Usage Documentation** - Transparent record of all AI-assisted decisions and code generation
- **Unit Tests** - Comprehensive test suite validates core logic and ensures pipeline robustness
- **Error Handling & Logging** - Production-grade monitoring and debugging capabilities

## Data Sources

| Source | API Endpoint | Description |
|--------|--------------|-------------|
| **NOAA Climate Data** | https://www.ncei.noaa.gov/cdo-web/api/v2 | Historical and real-time weather data |
| **U.S. EIA Electricity** | https://api.eia.gov/v2/electricity/rto/daily-region-data/data/ | Regional electricity demand data |

## Supported Cities

| City | State | NOAA Station ID | EIA Region | Population |
|------|-------|-----------------|------------|------------|
| New York | NY | GHCND:USW00094728 | NYIS | 8.3M |
| Chicago | IL | GHCND:USW00094846 | PJM | 2.7M |
| Houston | TX | GHCND:USW00012960 | ERCO | 2.3M |
| Phoenix | AZ | GHCND:USW00023183 | AZPS | 1.7M |
| Seattle | WA | GHCND:USW00024233 | SCL | 750K |

## Key Insights

### Temperature-Demand Correlation
Energy demand rises sharply with temperature extremes (both heating and cooling), creating clear correlation patterns visible in time series and statistical analysis.

### Seasonal Patterns
- **Summer Peaks**: High cooling demand during hot months
- **Winter Surges**: Increased heating requirements in cold periods
- **Shoulder Seasons**: Moderate, stable consumption patterns

### Behavioral Cycles
- **Weekday vs Weekend**: Distinct usage patterns reflecting commercial vs residential demand
- **Hourly Variations**: Peak usage during business hours and evening residential periods
- **Holiday Effects**: Reduced consumption during major holidays

### Regional Variations
Each city demonstrates unique energy-weather response profiles, enabling location-specific forecasting models and targeted grid management strategies.

## Data Quality Framework

Our automated validation system performs three critical checks after each data update:

### 1. Missing Value Detection
- **Scope**: Scans all columns for null entries
- **Impact**: Missing timestamps or values can distort downstream forecasting models
- **Action**: Flags incomplete records for manual review or interpolation

### 2. Outlier Detection
- **Temperature Filtering**: Removes unrealistic readings (>130°F, <-50°F)
- **Demand Validation**: Flags impossible consumption values (negative MW, extreme spikes)
- **Purpose**: Outliers often indicate sensor malfunctions or data ingestion errors

### 3. Data Freshness Verification
- **Check**: Ensures latest data is no more than 2 days old
- **Importance**: Guarantees decisions are based on current, relevant information
- **Alert**: Triggers notifications when data becomes stale

**Output**: Comprehensive quality report generated and archived with each pipeline run.

## Getting Started

### Prerequisites
- Python 3.8+
- [Poetry](https://python-poetry.org/) for dependency management
- API keys for NOAA and EIA services

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd energy-forecasting
```

2. **Install dependencies**
```bash
# Install all dependencies and create virtual environment
poetry install

# Optional: view the virtual environment path
poetry env info --path
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Usage

#### 1. Fetch Raw Data
```bash
poetry run python src/data_fetcher.py
```

#### 2. Run Data Pipeline
```bash
poetry run python src/pipeline.py
```

#### 3. Launch Dashboard
```bash
poetry run streamlit run dashboards/app.py
```

#### 4. Run Tests
```bash
poetry run pytest tests/
```

## Dashboard Preview

The Streamlit dashboard provides:
- **Interactive Maps**: Geographic visualization of energy consumption
- **Time Series Charts**: Historical trends and forecasting
- **Correlation Matrices**: Statistical relationships between variables
- **Performance Metrics**: Pipeline health and data quality indicators

## Project Structure

```
PROJECT1-ENERGY-ANALYSIS/
├── .pytest_cache/
├── config/
│   ├── __pycache__/
│   ├── config.yaml
│   └── constants.py
├── dashboards/
│   └── app.py
├── data/
│   ├── processed/
│   ├── raw/
│   └── reports/
├── logs/
├── notebooks/
├── src/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── analysis.py
│   ├── data_fetcher.py
│   ├── data_processor.py
│   ├── pipeline.py
│   └── visualizations.py
├── tests/
│   ├── __pycache__/
│   ├── conftest.py
│   ├── test_analysis.py
│   ├── test_data_fetcher.py
│   ├── test_data_processor.py
│   └── test_pipeline.py
├── .env
├── .gitignore
├── AI_USAGE.md
├── poetry.lock
├── pyproject.toml
├── pytest.ini
├── README.md
└── video_link.md
```

### Directory Overview

| Directory | Purpose |
|-----------|---------|
| `config/` | Configuration files and constants |
| `dashboards/` | Streamlit dashboard application |
| `data/` | Data storage (raw, processed, reports) |
| `logs/` | Application logs and debugging info |
| `notebooks/` | Jupyter notebooks for analysis |
| `src/` | Source code and core modules |
| `tests/` | Unit tests and test configurations |

### Key Files

| File | Description |
|------|-------------|
| `src/pipeline.py` | Main ETL pipeline orchestrator |
| `src/data_fetcher.py` | API data collection module |
| `src/data_processor.py` | Data cleaning and transformation |
| `src/analysis.py` | Statistical analysis and insights |
| `src/visualizations.py` | Chart generation and plotting |
| `dashboards/app.py` | Streamlit dashboard interface |
| `config/config.yaml` | Main configuration settings |
| `pyproject.toml` | Poetry dependencies and project metadata |
| `AI_USAGE.md` | Documentation of AI-assisted development |

## Configuration

The project uses a flexible configuration system:
- **`config/config.yaml`**: Main configuration file
- **`config/constants.py`**: Project constants and parameters
- **`.env`**: Environment variables and API keys

## Acknowledgments

- **NOAA** for providing comprehensive weather data
- **U.S. EIA** for electricity demand datasets
- **Open Source Community** for the excellent tools and libraries used in this project

---

*For questions or support, please open an issue or contact the development team.*