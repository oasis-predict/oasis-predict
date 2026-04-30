import requests
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
params = {
"limit": 100,
"status": "open"
} h
eaders = {
"Accept": "application/json",
"User-Agent": "weather-ai-agent/1.0"
} t
ry:
response = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
print("Status code:", response.status_code)
response.raise_for_status()
data = response.json()
print("Top-level keys:", list(data.keys()))
markets = data.get("markets", [])
print(f"Markets found: {len(markets)}")
print("=" * 80)
for market in markets[:20]:
print("Ticker :", market.get("ticker"))
print("Title :", market.get("title"))
print("Subtitle :", market.get("subtitle"))
print("Status :", market.get("status"))
print("Yes ask :", market.get("yes_ask"))
print("Yes bid :", market.get("yes_bid"))
print("No ask :", market.get("no_ask"))
print("No bid :", market.get("no_bid"))
print("Volume :", market.get("volume"))
print("-" * 80)
except requests.exceptions.RequestException as e:
print("Network/API error:", e)
except Exception as e:
print("Unexpected error:", e)
