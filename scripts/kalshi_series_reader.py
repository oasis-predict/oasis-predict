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

    data = response.json()
    series_list = data.get("series", [])

    print("Total series:", len(series_list))
    print("=" * 60)

    weather_series = []

    for s in series_list:
        text = f"{s.get('title','')} {s.get('subtitle','')} {s.get('category','')}".lower()

        if any(word in text for word in WEATHER_WORDS):
            weather_series.append(s)

    print("Weather series found:", len(weather_series))
    print("=" * 60)

    for s in weather_series:
        print("Ticker:", s.get("ticker"))
        print("Title :", s.get("title"))
        print("Category:", s.get("category"))
        print("-" * 60)

except Exception as e:
    print("Error:", e)
