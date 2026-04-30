import requests
from parse_kalshi_weather_market import parse_kalshi_question

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"

headers = {
    "Accept": "application/json",
    "User-Agent": "weather-ai-agent/1.0"
}

SERIES_TICKER = "KXHIGHLAX"

params = {
    "series_ticker": SERIES_TICKER,
    "limit": 200
}

try:
    response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)

    print("Status:", response.status_code)
    response.raise_for_status()

    data = response.json()
    markets = data.get("markets", [])

    print(f"Total markets for series {SERIES_TICKER}: {len(markets)}")
    print("=" * 90)

    parsed_count = 0

    for m in markets:
        title = m.get("title")
        status = m.get("status")

        if not title:
            continue

        if str(status).lower() not in ["active", "initialized", "open"]:
            continue

        parsed = parse_kalshi_question(title)

        print("TITLE         :", title)
        print("STATUS        :", status)
        print("CITY          :", parsed.get("city"))
        print("DATE          :", parsed.get("date"))
        print("MARKET TYPE   :", parsed.get("market_type"))
        print("COMPARISON    :", parsed.get("comparison"))
        print("THRESHOLD LOW :", parsed.get("threshold_low"))
        print("THRESHOLD HIGH:", parsed.get("threshold_high"))
        print("-" * 90)

        parsed_count += 1

    print(f"Parsed active/initialized markets: {parsed_count}")

except Exception as e:
    print("Error:", e)
