import re
import json
import os
from datetime import datetime

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
    r"\bseattle\b"
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

OUTPUT_JSON = "data/polymarket_weather_matches.json"
OUTPUT_LOG = "data/polymarket_weather_watcher.log"


def matches_any(patterns, text):
    return any(re.search(pattern, text) for pattern in patterns)


def is_weather_market(question: str) -> bool:
    question = question.lower()

    if matches_any(EXCLUDE_PATTERNS, question):
        return False

    has_weather_word = matches_any(WEATHER_PATTERNS, question)
    has_city = matches_any(CITY_PATTERNS, question)

    return has_weather_word or (has_city and has_weather_word)


def append_log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


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

        matches = []

        for market in markets:
            question = market.get("question") or ""
            if is_weather_market(question):
                matches.append({
                    "question": market.get("question"),
                    "slug": market.get("slug"),
                    "endDate": market.get("endDate"),
                    "outcomes": market.get("outcomes"),
                    "outcomePrices": market.get("outcomePrices"),
                    "bestBid": market.get("bestBid"),
                    "bestAsk": market.get("bestAsk"),
                    "id": market.get("id"),
                    "conditionId": market.get("conditionId"),
                    "clobTokenIds": market.get("clobTokenIds")
                })

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)

        print(f"Total markets fetched: {len(markets)}")
        print(f"Weather markets found: {len(matches)}")

        if len(matches) == 0:
            print("No active weather markets found right now.")
            append_log("No active weather markets found")
        else:
            print("=" * 80)
            print("ACTIVE WEATHER MARKETS FOUND")
            print("=" * 80)

            for market in matches:
                print("Question:", market["question"])
                print("Slug:", market["slug"])
                print("End date:", market["endDate"])
                print("Outcomes:", market["outcomes"])
                print("Outcome prices:", market["outcomePrices"])
                print("Best bid:", market["bestBid"])
                print("Best ask:", market["bestAsk"])
                print("Market ID:", market["id"])
                print("Condition ID:", market["conditionId"])
                print("CLOB token IDs:", market["clobTokenIds"])
                print("-" * 80)

            append_log(f"Found {len(matches)} active weather market(s)")

    except requests.exceptions.RequestException as e:
        print("Network/API error:", e)
        append_log(f"Network/API error: {e}")

    except Exception as e:
        print("Unexpected error:", e)
        append_log(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
