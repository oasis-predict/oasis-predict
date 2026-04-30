import re
import requests

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"

params = {
    "active": "true",
    "closed": "false",
    "limit": 1000
}

headers = {
    "User-Agent": "weather-ai-agent/1.0",
    "Accept": "application/json"
}

# mots vraiment météo
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

# villes cibles, mais elles ne suffisent pas à elles seules
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

# mots à exclure pour éviter les faux positifs
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
    r"\bopenai\b"
]

def matches_any(patterns, text):
    return any(re.search(pattern, text) for pattern in patterns)

try:
    response = requests.get(
        GAMMA_MARKETS_URL,
        params=params,
        headers=headers,
        timeout=30
    )

    print("Status code:", response.status_code)
    response.raise_for_status()

    markets = response.json()

    if not isinstance(markets, list):
        print("Unexpected API response:")
        print(markets)
        raise SystemExit(1)

    print(f"Total markets fetched: {len(markets)}")
    print("=" * 80)

    print("SAMPLE QUESTIONS FROM POLYMARKET:")
    print("=" * 80)
    for market in markets[:20]:
        print("-", market.get("question", "N/A"))

    print("\n" + "=" * 80)
    print("STRICT WEATHER MARKETS:")
    print("=" * 80)

    matches = []

    for market in markets:
        question_raw = market.get("question") or ""
        question = question_raw.lower()

        # exclure les marchés évidemment non météo
        if matches_any(EXCLUDE_PATTERNS, question):
            continue

        # il faut soit:
        # 1) un vrai mot météo
        # ou
        # 2) une ville + un mot météo
        has_weather_word = matches_any(WEATHER_PATTERNS, question)
        has_city = matches_any(CITY_PATTERNS, question)

        if has_weather_word or (has_city and has_weather_word):
            matches.append(market)

    print(f"Strict weather markets found: {len(matches)}")
    print("=" * 80)

    if len(matches) == 0:
        print("No real active weather markets found right now.")
        print("That is normal. Polymarket may not currently have active weather markets.")

    for market in matches:
        print("Question:", market.get("question", "N/A"))
        print("Slug:", market.get("slug", "N/A"))
        print("End date:", market.get("endDate", "N/A"))
        print("Outcomes:", market.get("outcomes", []))
        print("Outcome prices:", market.get("outcomePrices", []))
        print("Best bid:", market.get("bestBid", "N/A"))
        print("Best ask:", market.get("bestAsk", "N/A"))
        print("Market ID:", market.get("id", "N/A"))
        print("Condition ID:", market.get("conditionId", "N/A"))
        print("CLOB token IDs:", market.get("clobTokenIds", "N/A"))
        print("-" * 80)

except requests.exceptions.RequestException as e:
    print("Network/API error:", e)

except ValueError as e:
    print("JSON decode error:", e)

except Exception as e:
    print("Unexpected error:", e)
