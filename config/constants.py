CITY_TIMEZONE_MAP = {
    "New York": "America/New_York",
    "Chicago": "America/Chicago",
    "Houston": "America/Chicago",
    "Phoenix": "America/Phoenix",
    "Seattle": "America/Los_Angeles",
}

CITY_COORDS_MAP = {
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "Chicago": {"lat": 41.8781, "lon": -87.6298},
    "Houston": {"lat": 29.7604, "lon": -95.3698},
    "Phoenix": {"lat": 33.4484, "lon": -112.0740},
    "Seattle": {"lat": 47.6062, "lon": -122.3321},
}

def standardize_city(city: str) -> str:
    return city.strip().title() if isinstance(city, str) else city