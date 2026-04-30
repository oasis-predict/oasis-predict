
import re
import json
import os
from datetime import datetime, timedelta

import requests

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"

PARAMS = {
    "active": "true",
    "closed": "false",
    "limit": 1000
}

HEADERS = {
    "User-Agent": "weather-ai-agent/1.0",
    "Accept": "application/json"
}

OUTPUT_JSON = "data/polymarket_weather_parsed.json"
OUTPUT_LOG = "data/polymarket_weather_pipeline.log"

TODAY = datetime(2026, 3, 18)

KNOWN_CITIES = [
    "Shanghai",
    "Paris",
    "London",
    "Seoul",
    "Tokyo",
    "New York",
    "Toronto",
    "Singapore",
    "Chicago",
    "Dallas",
    "Seattle",
    "Munich",
    "Berlin",
    "Madrid",
    "Rome",
    "Luxembourg"
]

WEATHER_PATTERNS = [
    r"\bweather\b",
    r"\brain\b",
    r"\bsnow\b",
    r"\bstorm\b",
    r"\bwind\b",
    r"\btemperature\b",
    r"\btemp\b",
    r"\bhighest temperature\b",
    r"\blowest temperature\b",
    r"\bdegrees?\b",
    r"\bcelsius\b",
    r"\bfahrenheit\b",
    r"\bprecipitation\b",
    r"\bhumidity\b",
    r"\bforecast\b"
]

CITY_PATTERNS = [
    r"\bshanghai\b",
    r"\bparis\b",
    r"\blondon\b",
    r"\bseoul\b",
    r"\btokyo\b",
    r"\bnew york\b",
    r"\btoronto\b",
    r"\bsingapore\b",
    r"\bchicago\b",
    r"\bdallas\b",
    r"\bseattle\b",
    r"\bmunich\b",
    r"\bberlin\b",
    r"\bmadrid\b",
    r"\brome\b",
    r"\bluxembourg\b"
]

EXCLUDE_PATTERNS = [
    r"\bnba\b",
    r"\bnhl\b",
    r"\bfifa\b",
    r"\bworld cup\b",
    r"\bstanley cup\b",
    r"\bfinals\b",
    r"\bconference\b",
    r"\bpresident\b",
    r"\bceasefire\b",
    r"\bukraine\b",
    r"\brussia\b",
    r"\bbitcoin\b",
    r"\bgta\b",
    r"\balbum\b",
    r"\bopenai\b",
    r"\bmavericks\b",
    r"\braptors\b",
    r"\blakers\b",
    r"\bceltics\b"
]


def append_log(message: str) -> None:
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def matches_any(patterns, text):
    return any(re.search(pattern, text) for pattern in patterns)


def is_weather_market(question: str) -> bool:
    q = (question or "").lower()

    if matches_any(EXCLUDE_PATTERNS, q):
        return False

    has_weather_word = matches_any(WEATHER_PATTERNS, q)
    has_city = matches_any(CITY_PATTERNS, q)

    return has_weather_word or (has_city and has_weather_word)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_city(question: str):
    for city in sorted(KNOWN_CITIES, key=len, reverse=True):
        pattern = r"\b" + re.escape(city) + r"\b"
        if re.search(pattern, question, flags=re.IGNORECASE):
            return city
    return None


def parse_date(question: str):
    q = question.lower()

    if "today" in q:
        return TODAY.strftime("%Y-%m-%d")

    if "tomorrow" in q:
        return (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")

    if "yesterday" in q:
        return (TODAY - timedelta(days=1)).strftime("%Y-%m-%d")

    month_map = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    pattern = re.search(
        r"\b("
        + "|".join(month_map.keys())
        + r")\s+(\d{1,2})(?:,\s*(\d{4}))?\b",
        q,
    )

    if pattern:
        month_name = pattern.group(1)
        day = int(pattern.group(2))
        year = int(pattern.group(3)) if pattern.group(3) else TODAY.year
        month = month_map[month_name]

        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    return None


def parse_threshold(question: str):
    q = question.lower()

    patterns = [
        r"(?:exceed|above|over|greater than|higher than)\s*(-?\d+(?:\.\d+)?)\s*(?:°c|c|degrees?)?",
        r"(?:below|under|less than|lower than)\s*(-?\d+(?:\.\d+)?)\s*(?:°c|c|degrees?)?",
        r"(-?\d+(?:\.\d+)?)\s*(?:°c|c|degrees?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

    return None


def detect_market_type(question: str):
    q = question.lower()

    if "highest temperature" in q or "high temperature" in q or "max temperature" in q:
        return "daily_high_temperature"

    if "lowest temperature" in q or "low temperature" in q or "min temperature" in q:
        return "daily_low_temperature"

    if "rain" in q or "precipitation" in q:
        return "rain_event"

    if "snow" in q:
        return "snow_event"

    if "wind" in q:
        return "wind_event"

    if "humidity" in q:
        return "humidity_event"

    if "temperature" in q or "temp" in q:
        return "temperature_event"

    return "unknown"


def detect_comparison(question: str):
    q = question.lower()

    if any(x in q for x in ["exceed", "above", "over", "greater than", "higher than"]):
        return "greater_than"

    if any(x in q for x in ["below", "under", "less than", "lower than"]):
        return "less_than"

    if "between" in q:
        return "between"

    return None


def detect_market_mode(question: str, outcomes=None):
    q = question.lower()
    outcomes = outcomes or []
    outcomes_lower = [str(x).lower() for x in outcomes]

    if "yes" in outcomes_lower and "no" in outcomes_lower:
        return "binary"

    if q.startswith("will "):
        return "binary"

    if "highest temperature" in q or "lowest temperature" in q:
        if len(outcomes) > 2:
            return "multi_outcome"
        return "temperature_range_or_binary"

    if len(outcomes) > 2:
        return "multi_outcome"

    return "unknown"


def parse_question(question: str, outcomes=None):
    question = normalize_spaces(question)

    return {
        "raw_question": question,
        "city": parse_city(question),
        "date": parse_date(question),
        "market_type": detect_market_type(question),
        "comparison": detect_comparison(question),
        "threshold": parse_threshold(question),
        "mode": detect_market_mode(question, outcomes),
        "outcomes": outcomes or []
    }


def main():
    os.makedirs("data", exist_ok=True)

    try:
        response = requests.get(
            GAMMA_MARKETS_URL,
            params=PARAMS,
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()

        markets = response.json()

        if not isinstance(markets, list):
            print("Unexpected API response")
            append_log("Unexpected API response format")
            return

        weather_markets = []

        for market in markets:
            question = market.get("question") or ""

            if not is_weather_market(question):
                continue

            outcomes = market.get("outcomes", [])
            parsed = parse_question(question, outcomes)

            enriched_market = {
                "question": question,
                "slug": market.get("slug"),
                "endDate": market.get("endDate"),
                "outcomes": outcomes,
                "outcomePrices": market.get("outcomePrices"),
                "bestBid": market.get("bestBid"),
                "bestAsk": market.get("bestAsk"),
                "id": market.get("id"),
                "conditionId": market.get("conditionId"),
                "clobTokenIds": market.get("clobTokenIds"),
                "parsed": parsed
            }

            weather_markets.append(enriched_market)

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(weather_markets, f, indent=2, ensure_ascii=False)

        print(f"Total markets fetched: {len(markets)}")
        print(f"Parsed weather markets found: {len(weather_markets)}")

        if len(weather_markets) == 0:
            print("No active weather markets found right now.")
            append_log("No active weather markets found")
            return

        print("=" * 90)
        print("PARSED WEATHER MARKETS")
        print("=" * 90)

        for market in weather_markets:
            parsed = market["parsed"]

            print("Question      :", market["question"])
            print("City          :", parsed["city"])
            print("Date          :", parsed["date"])
            print("Market type   :", parsed["market_type"])
            print("Comparison    :", parsed["comparison"])
            print("Threshold     :", parsed["threshold"])
            print("Mode          :", parsed["mode"])
            print("Outcomes      :", market["outcomes"])
            print("Prices        :", market["outcomePrices"])
            print("Best bid      :", market["bestBid"])
            print("Best ask      :", market["bestAsk"])
            print("Slug          :", market["slug"])
            print("-" * 90)

        append_log(f"Parsed {len(weather_markets)} weather market(s) successfully")

    except requests.exceptions.RequestException as e:
        print("Network/API error:", e)
        append_log(f"Network/API error: {e}")

    except Exception as e:
        print("Unexpected error:", e)
        append_log(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
