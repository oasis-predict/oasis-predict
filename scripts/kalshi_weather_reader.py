import requests

url = "https://api.elections.kalshi.com/trade-api/v2/markets"

try:
    r = requests.get(url, timeout=10)
    print("Status:", r.status_code)

    data = r.json()
    markets = data.get("markets", [])

    print("Total markets:", len(markets))
    print("=" * 50)

    for m in markets[:10]:
        print("Title:", m.get("title"))
        print("Yes ask:", m.get("yes_ask"))
        print("No ask:", m.get("no_ask"))
        print("-" * 50)

except Exception as e:
    print("Error:", e)
