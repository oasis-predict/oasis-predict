import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

import requests


AGENT_NAME = "Oasis__Duc_Haven_Weather"
NOAA_POINTS_URL = "https://api.weather.gov/points/{lat:.4f},{lon:.4f}"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MET_NORWAY_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"
NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
USER_AGENT = "Oasis__Duc_Haven_Weather/1.0 (local weather research agent)"


CITY_SETTINGS = {
    "LA": {
        "name": "Los Angeles",
        "aliases": {"la", "l.a.", "los angeles", "lax"},
        "lat": 34.0522,
        "lon": -118.2437,
        "timezone": "America/Los_Angeles",
    },
    "NYC": {
        "name": "New York",
        "aliases": {"nyc", "new york", "new york city", "manhattan"},
        "lat": 40.7128,
        "lon": -74.0060,
        "timezone": "America/New_York",
    },
    "MIAMI": {
        "name": "Miami",
        "aliases": {"miami", "mia"},
        "lat": 25.7617,
        "lon": -80.1918,
        "timezone": "America/New_York",
    },
}


@dataclass(frozen=True)
class TemperatureEstimate:
    source: str
    high_f: float
    weight: float
    official: bool
    detail: str


def c_to_f(temp_c: float) -> float:
    return (temp_c * 9.0 / 5.0) + 32.0


def round_float(value: Optional[float], digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), digits)


def normalize_city(city_text: str) -> str:
    normalized = re.sub(r"[^a-z. ]+", " ", city_text.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)

    for city_code, settings in CITY_SETTINGS.items():
        if normalized in settings["aliases"] or normalized == city_code.lower():
            return city_code
    raise ValueError(f"Unknown city for {AGENT_NAME}: {city_text}")


def city_from_question(question: str) -> str:
    lower = question.lower()
    for city_code, settings in CITY_SETTINGS.items():
        if any(alias in lower for alias in settings["aliases"]):
            return city_code
    raise ValueError("Question must mention LA, NYC/New York, or Miami.")


def today_for_city(city_code: str) -> str:
    timezone = ZoneInfo(CITY_SETTINGS[city_code]["timezone"])
    return datetime.now(timezone).date().isoformat()


def safe_get(data: dict, *keys: str, default=None):
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def get_json(
    url: str,
    params: Optional[dict[str, Any]] = None,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def parse_iso_local_date(timestamp: str, timezone_name: str) -> Optional[str]:
    if not timestamp:
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return timestamp[:10] if len(timestamp) >= 10 else None
    return dt.astimezone(ZoneInfo(timezone_name)).date().isoformat()


def noaa_high(city_code: str, target_date: str, http_get_json: Callable = get_json) -> TemperatureEstimate:
    settings = CITY_SETTINGS[city_code]
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    points_url = NOAA_POINTS_URL.format(lat=settings["lat"], lon=settings["lon"])
    point_data = http_get_json(points_url, headers=headers)
    properties = point_data.get("properties", {})

    hourly_url = properties.get("forecastHourly")
    if hourly_url:
        hourly_data = http_get_json(hourly_url, headers=headers)
        temps = []
        for period in safe_get(hourly_data, "properties", "periods", default=[]):
            if parse_iso_local_date(period.get("startTime", ""), settings["timezone"]) != target_date:
                continue
            temp = period.get("temperature")
            if temp is None:
                continue
            value = float(temp)
            if str(period.get("temperatureUnit", "F")).upper() == "C":
                value = c_to_f(value)
            temps.append(value)
        if temps:
            return TemperatureEstimate("NOAA/NWS hourly", max(temps), 0.46, True, "official USA hourly forecast")

    forecast_url = properties.get("forecast")
    if forecast_url:
        forecast_data = http_get_json(forecast_url, headers=headers)
        temps = []
        for period in safe_get(forecast_data, "properties", "periods", default=[]):
            if not period.get("isDaytime"):
                continue
            if parse_iso_local_date(period.get("startTime", ""), settings["timezone"]) != target_date:
                continue
            temp = period.get("temperature")
            if temp is None:
                continue
            value = float(temp)
            if str(period.get("temperatureUnit", "F")).upper() == "C":
                value = c_to_f(value)
            temps.append(value)
        if temps:
            return TemperatureEstimate("NOAA/NWS daily", max(temps), 0.46, True, "official USA daily forecast")

    raise RuntimeError("NOAA/NWS did not return a usable high temperature forecast.")


def open_meteo_high(city_code: str, target_date: str, http_get_json: Callable = get_json) -> TemperatureEstimate:
    settings = CITY_SETTINGS[city_code]
    params = {
        "latitude": settings["lat"],
        "longitude": settings["lon"],
        "daily": "temperature_2m_max",
        "hourly": "temperature_2m",
        "temperature_unit": "fahrenheit",
        "timezone": settings["timezone"],
        "start_date": target_date,
        "end_date": target_date,
    }
    data = http_get_json(OPEN_METEO_URL, params=params)
    daily = data.get("daily", {})
    for date_value, temp in zip(daily.get("time", []), daily.get("temperature_2m_max", [])):
        if date_value == target_date and temp is not None:
            return TemperatureEstimate("Open-Meteo", float(temp), 0.24, False, "multi-model normalized forecast")

    hourly = data.get("hourly", {})
    temps = [
        float(temp)
        for date_value, temp in zip(hourly.get("time", []), hourly.get("temperature_2m", []))
        if str(date_value).startswith(target_date) and temp is not None
    ]
    if temps:
        return TemperatureEstimate("Open-Meteo hourly", max(temps), 0.24, False, "multi-model hourly forecast")

    raise RuntimeError("Open-Meteo did not return a usable high temperature forecast.")


def met_norway_high(city_code: str, target_date: str, http_get_json: Callable = get_json) -> TemperatureEstimate:
    settings = CITY_SETTINGS[city_code]
    params = {"lat": settings["lat"], "lon": settings["lon"]}
    headers = {"User-Agent": USER_AGENT}
    data = http_get_json(MET_NORWAY_URL, params=params, headers=headers)

    temps = []
    for item in safe_get(data, "properties", "timeseries", default=[]):
        if parse_iso_local_date(item.get("time", ""), settings["timezone"]) != target_date:
            continue
        temp_c = safe_get(item, "data", "instant", "details", "air_temperature")
        if temp_c is not None:
            temps.append(c_to_f(float(temp_c)))

    if temps:
        return TemperatureEstimate("MET Norway", max(temps), 0.20, True, "official Norwegian model forecast")
    raise RuntimeError("MET Norway did not return a usable high temperature forecast.")


def nasa_power_high(city_code: str, target_date: str, http_get_json: Callable = get_json) -> TemperatureEstimate:
    settings = CITY_SETTINGS[city_code]
    ymd = target_date.replace("-", "")
    params = {
        "parameters": "T2M_MAX",
        "community": "RE",
        "longitude": settings["lon"],
        "latitude": settings["lat"],
        "start": ymd,
        "end": ymd,
        "format": "JSON",
    }
    data = http_get_json(NASA_POWER_URL, params=params)
    value = safe_get(data, "properties", "parameter", "T2M_MAX", ymd)
    if value is None or float(value) < -900:
        raise RuntimeError("NASA POWER has no finalized daily high for this date yet.")
    return TemperatureEstimate("NASA POWER", c_to_f(float(value)), 0.10, True, "official NASA daily monitor")


def weighted_mean(estimates: list[TemperatureEstimate]) -> float:
    total_weight = sum(item.weight for item in estimates)
    return sum(item.high_f * item.weight for item in estimates) / total_weight


def weighted_std(estimates: list[TemperatureEstimate], mean_f: float) -> float:
    total_weight = sum(item.weight for item in estimates)
    variance = sum(item.weight * ((item.high_f - mean_f) ** 2) for item in estimates) / total_weight
    return math.sqrt(max(variance, 0.0))


def consensus_from_estimates(estimates: list[TemperatureEstimate]) -> dict[str, Any]:
    if not estimates:
        raise RuntimeError("No weather source returned a usable temperature.")

    noaa_present = any(item.source.startswith("NOAA/NWS") for item in estimates)
    official_count = sum(1 for item in estimates if item.official)
    source_count = len(estimates)
    mean_f = weighted_mean(estimates)
    std_f = weighted_std(estimates, mean_f)
    values = [item.high_f for item in estimates]
    spread_f = max(values) - min(values)
    confidence = max(0.0, min(1.0, 1.0 - (std_f / 4.0)))

    exact_band_ok = std_f <= 0.50
    buy_yes_allowed = noaa_present and source_count >= 3 and official_count >= 2 and exact_band_ok and spread_f <= 1.50

    return {
        "agent": AGENT_NAME,
        "estimated_high_f": round_float(mean_f),
        "std_dev_f": round_float(std_f),
        "spread_f": round_float(spread_f),
        "confidence": round_float(confidence, 3),
        "source_count": source_count,
        "official_source_count": official_count,
        "noaa_is_aggregator": noaa_present,
        "target_std_dev_f": 0.50,
        "exact_band_ok": exact_band_ok,
        "trade_signal": "BUY_YES" if buy_yes_allowed else "NO_TRADE",
        "decision_reason": (
            "NOAA present and consensus std <= 0.50 F"
            if buy_yes_allowed
            else "Consensus is not tight enough for BUY_YES"
        ),
        "sources": [
            {
                "source": item.source,
                "high_f": round_float(item.high_f),
                "weight": item.weight,
                "official": item.official,
                "detail": item.detail,
            }
            for item in estimates
        ],
    }


def get_high_temperature_consensus(city_code: str, target_date: Optional[str] = None) -> dict[str, Any]:
    city_code = normalize_city(city_code)
    target_date = target_date or today_for_city(city_code)
    estimates = []
    errors = {}

    for fetcher in (noaa_high, open_meteo_high, met_norway_high, nasa_power_high):
        try:
            estimates.append(fetcher(city_code, target_date))
        except Exception as exc:
            errors[fetcher.__name__] = str(exc)

    result = consensus_from_estimates(estimates)
    result.update(
        {
            "city": CITY_SETTINGS[city_code]["name"],
            "city_code": city_code,
            "target_date": target_date,
            "errors": errors,
        }
    )
    return result


def answer_high_temperature_question(question: str) -> dict[str, Any]:
    city_code = city_from_question(question)
    return get_high_temperature_consensus(city_code, today_for_city(city_code))


def format_answer(result: dict[str, Any]) -> str:
    lines = [
        f"{result['agent']} - {result['city']} high on {result['target_date']}",
        f"Estimated high: {result['estimated_high_f']} F",
        f"Consensus std dev: {result['std_dev_f']} F",
        f"Spread: {result['spread_f']} F",
        f"Signal: {result['trade_signal']} ({result['decision_reason']})",
        "Sources:",
    ]
    for item in result["sources"]:
        official = "official" if item["official"] else "derived"
        lines.append(f"- {item['source']}: {item['high_f']} F, weight {item['weight']} ({official})")
    if result.get("errors"):
        lines.append("Source errors:")
        for source, error in result["errors"].items():
            lines.append(f"- {source}: {error}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{AGENT_NAME} exact high-temperature consensus agent")
    parser.add_argument("--city", choices=sorted(CITY_SETTINGS), help="City code: LA, NYC, or MIAMI")
    parser.add_argument("--date", help="Target date as YYYY-MM-DD. Defaults to local today for the city.")
    parser.add_argument("--question", help='Example: "Highest temperature in LA today?"')
    parser.add_argument("--json", action="store_true", help="Print raw JSON output")
    return parser


def main(argv: Optional[list[str]] = None) -> dict[str, Any]:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.question:
        result = answer_high_temperature_question(args.question)
    else:
        city_code = args.city or "LA"
        result = get_high_temperature_consensus(city_code, args.date)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_answer(result))

    return result


if __name__ == "__main__":
    main()
