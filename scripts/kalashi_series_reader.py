import requests

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/series"

headers = {
    "Accept": "application/json",
    "User-Agent": "weather-ai-agent/1.0"
}

params = {
    "limit": 200
}

WEATHER_WORDS = [
    "weather",
    "climate",
    "temperature",
    "rain",
    "snow",
    "wind"
]

try:
    response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
    print("Status:", response.status_code)
    response.raise_for_status()

    data = response.json()
    print("Top-level keys:", list(data.keys()))

    series_list = data.get("series", [])
    print("Total series:", len(series_list))
    print("=" * 80)

    matches = []

    for s in series_list:
        text = " ".join([
            str(s.get("title", "")),
            str(s.get("subtitle", "")),
            str(s.get("ticker", "")),
            str(s.get("category", ""))
        ]).lower()

        if any(word in text for word in WEATHER_WORDS):
            matches.append(s)

    print("Weather-related series found:", len(matches))
    print("=" * 80)

    for s in matches:
        print("Ticker   :", s.get("ticker"))
        print("Title    :", s.get("title"))
        print("Subtitle :", s.get("subtitle"))
        print("Category :", s.get("category"))
        print("-" * 80)

except Exception as e:
    print("Error:", e)
