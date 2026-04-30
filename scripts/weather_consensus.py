import os
import math
import requests
from datetime import datetime, UTC
from typing import Optional, Dict, Any

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NOAA_POINTS_URL = "https://api.weather.gov/points/{lat},{lon}"
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Coordonnées de base — ajuste si besoin
CITY_COORDS = {
    "LA": {"lat": 33.9425, "lon": -118.4081},        # LAX
    "NYC": {"lat": 40.7812, "lon": -73.9665},        # Central Park approx
    "Chicago": {"lat": 41.7868, "lon": -87.7522},    # Midway
}

USER_AGENT = "weather-ai-agent/1.0 (contact: local-dev)"


def c_to_f(temp_c: float) -> float:
    return (temp_c * 9.0 / 5.0) + 32.0


def safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def round_or_none(x: Optional[float], ndigits: int = 2) -> Optional[float]:
    return None if x is None else round(x, ndigits)


def get_openmeteo_daily_max(lat: float, lon: float, target_date: str) -> Optional[float]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "start_date": target_date,
        "end_date": target_date,
        # optionnel: "models": "best_match"
    }
    r = requests.get(OPEN_METEO_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    dates = safe_get(data, "daily", "time", default=[])
    temps = safe_get(data, "daily", "temperature_2m_max", default=[])

    for d, t in zip(dates, temps):
        if d == target_date:
            return float(t)
    return None


def get_noaa_daily_max(lat: float, lon: float, target_date: str) -> Optional[float]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}

    # 1) récupérer l'URL forecast
    points_url = NOAA_POINTS_URL.format(lat=lat, lon=lon)
    r = requests.get(points_url, headers=headers, timeout=20)
    r.raise_for_status()
    points = r.json()

    forecast_url = safe_get(points, "properties", "forecast")
    if not forecast_url:
        return None

    # 2) récupérer les périodes de forecast
    r2 = requests.get(forecast_url, headers=headers, timeout=20)
    r2.raise_for_status()
    forecast = r2.json()

    periods = safe_get(forecast, "properties", "periods", default=[])

    day_values = []
    for p in periods:
        # NOAA renvoie des périodes "day/night"
        start_time = p.get("startTime", "")
        is_daytime = p.get("isDaytime", False)
        temp = p.get("temperature")

        if not start_time or temp is None:
            continue

        day = start_time[:10]
        if day == target_date and is_daytime:
            # selon l'unité renvoyée
            unit = p.get("temperatureUnit", "F")
            val = float(temp)
            if unit.upper() == "C":
                val = c_to_f(val)
            day_values.append(val)

    if not day_values:
        return None
    return max(day_values)


def get_nasa_monitor_temp(lat: float, lon: float, target_date: str) -> Optional[float]:
    # NASA POWER est surtout utile ici comme monitoring / contrôle.
    # On récupère un paramètre de température journalière et on convertit si nécessaire.
    # Selon l’usage futur, tu pourras changer le paramètre.
    ymd = target_date.replace("-", "")
    params = {
        "parameters": "T2M_MAX",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": ymd,
        "end": ymd,
        "format": "JSON",
    }
    r = requests.get(NASA_POWER_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    raw = safe_get(data, "properties", "parameter", "T2M_MAX", default={})
    if ymd not in raw:
        return None

    val_c = raw.get(ymd)
    if val_c is None or (isinstance(val_c, (int, float)) and val_c < -900):
        return None

    return c_to_f(float(val_c))


def compute_consensus(
    openmeteo_temp: Optional[float],
    noaa_temp: Optional[float],
    nasa_monitor_temp: Optional[float],
    yes_spread_threshold_f: float = 2.0,
    skip_spread_threshold_f: float = 4.0,
) -> Dict[str, Any]:
    sources = {
        "openmeteo_temp": openmeteo_temp,
        "noaa_temp": noaa_temp,
        "nasa_monitor_temp": nasa_monitor_temp,
    }

    primary = [x for x in [openmeteo_temp, noaa_temp] if x is not None]
    all_vals = [x for x in sources.values() if x is not None]

    consensus_temp = None
    spread = None
    consensus_ok = False
    yes_allowed = False

    if len(primary) >= 2:
        consensus_temp = sum(primary) / len(primary)
        spread = max(primary) - min(primary)
        consensus_ok = spread <= skip_spread_threshold_f
        yes_allowed = spread <= yes_spread_threshold_f
    elif len(primary) == 1:
        consensus_temp = primary[0]
        spread = None
        consensus_ok = False
        yes_allowed = False

    # NASA ne décide pas seul, mais peut servir de drapeau d'alerte
    nasa_alert = False
    if consensus_temp is not None and nasa_monitor_temp is not None:
        nasa_alert = abs(nasa_monitor_temp - consensus_temp) > 6.0

    return {
        **{k: round_or_none(v) for k, v in sources.items()},
        "consensus_temp": round_or_none(consensus_temp),
        "spread": round_or_none(spread),
        "consensus_ok": consensus_ok,
        "yes_allowed": yes_allowed and not nasa_alert,
        "nasa_alert": nasa_alert,
    }


def get_city_weather_consensus(city: str, target_date: str) -> Dict[str, Any]:
    if city not in CITY_COORDS:
        raise ValueError(f"Unknown city: {city}")

    lat = CITY_COORDS[city]["lat"]
    lon = CITY_COORDS[city]["lon"]

    om = None
    noaa = None
    nasa = None
    errors = {}

    try:
        om = get_openmeteo_daily_max(lat, lon, target_date)
    except Exception as e:
        errors["openmeteo"] = str(e)

    try:
        noaa = get_noaa_daily_max(lat, lon, target_date)
    except Exception as e:
        errors["noaa"] = str(e)

    try:
        nasa = get_nasa_monitor_temp(lat, lon, target_date)
    except Exception as e:
        errors["nasa"] = str(e)

    result = compute_consensus(om, noaa, nasa)
    result.update({
        "city": city,
        "target_date": target_date,
        "errors": errors,
    })
    return result


if __name__ == "__main__":
    target = "2026-04-17"
    for city in ["LA", "NYC", "Chicago"]:
        out = get_city_weather_consensus(city, target)
        print(out)
