import requests

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
    print("=" * 80)

    open_markets = []

    for m in markets:
        status = str(m.get("status", "")).lower()

        yes_ask = m.get("yes_ask")
        yes_bid = m.get("yes_bid")
        no_ask = m.get("no_ask")
        no_bid = m.get("no_bid")

        is_tradeable = (
            status in ["open", "active", "initialized"]
            or yes_ask is not None
            or yes_bid is not None
            or no_ask is not None
            or no_bid is not None
        )

        if is_tradeable:
            open_markets.append(m)

    print(f"Open/tradeable markets found: {len(open_markets)}")
    print("=" * 80)

    for m in open_markets:
        print("Ticker      :", m.get("ticker"))
        print("Title       :", m.get("title"))
        print("Status      :", m.get("status"))
        print("Yes ask     :", m.get("yes_ask"))
        print("Yes bid     :", m.get("yes_bid"))
        print("No ask      :", m.get("no_ask"))
        print("No bid      :", m.get("no_bid"))
        print("Volume      :", m.get("volume"))
        print("-" * 80)

except Exception as e:
    print("Error:", e)
