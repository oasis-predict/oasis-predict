import json
import requests

TICKER = "KXHIGHLAX-26MAR19-T90"
BASE_URL = f"https://api.elections.kalshi.com/trade-api/v2/markets/{TICKER}"

headers = {
    "Accept": "application/json",
    "User-Agent": "weather-ai-agent/1.0"
}

try:
    response = requests.get(BASE_URL, headers=headers, timeout=30)

    print("Status:", response.status_code)
    response.raise_for_status()

    data = response.json()

    print("=" * 80)
    print("TOP LEVEL TYPE:", type(data))
    if isinstance(data, dict):
        print("TOP LEVEL KEYS:", list(data.keys()))
    print("=" * 80)
    print(json.dumps(data, indent=2))
    print("=" * 80)

except Exception as e:
    print("Error:", e)
