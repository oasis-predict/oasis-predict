import csv
import os
import requests
from datetime import datetime

from parse_kalshi_weather_market import parse_kalshi_question
from kalshi_probability_engine import estimate_probability_from_question

BASE_LIST_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
BASE_DETAIL_URL = "https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"

headers = {
    "Accept": "application/json",
    "User-Agent": "weather-ai-agent/1.0"
}

SERIES_TICKER = "KXHIGHLAX"
EDGE_THRESHOLD = 10.0
OUTPUT_FILE = "data/kalshi_decisions.csv"


def ensure_csv_exists():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "ticker",
                "title",
                "status",
                "city",
                "date",
                "market_type",
                "comparison",
                "threshold_low",
                "threshold_high",
                "predicted_temp_f",
                "ai_probability_yes",
                "yes_ask_percent",
                "yes_bid_percent",
                "no_ask_percent",
                "no_bid_percent",
                "last_price_percent",
                "edge_vs_yes_ask",
                "decision"
            ])


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def dollars_to_percent(value):
    if value is None:
        return None
    return round(value * 100, 2)


def fetch_market_detail(ticker):
    url = BASE_DETAIL_URL.format(ticker=ticker)
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("market", {})


def main():
    ensure_csv_exists()

    params = {
        "series_ticker": SERIES_TICKER,
        "limit": 200
    }

    response = requests.get(BASE_LIST_URL, params=params, headers=headers, timeout=30)
    print("Status:", response.status_code)
    response.raise_for_status()

    data = response.json()
    markets = data.get("markets", [])

    rows = []

    for m in markets:
        title = m.get("title")
        status = str(m.get("status", "")).lower()
        ticker = m.get("ticker")

        if not title or not ticker:
            continue

        if status not in ["active", "initialized", "open"]:
            continue

        parsed = parse_kalshi_question(title)
        prob_result = estimate_probability_from_question(title)

        ai_prob = prob_result.get("ai_probability_yes")
        pred_temp = prob_result.get("predicted_temp")

        detail = fetch_market_detail(ticker)

        yes_ask = safe_float(detail.get("yes_ask_dollars"))
        yes_bid = safe_float(detail.get("yes_bid_dollars"))
        no_ask = safe_float(detail.get("no_ask_dollars"))
        no_bid = safe_float(detail.get("no_bid_dollars"))
        last_price = safe_float(detail.get("last_price_dollars"))

        yes_ask_pct = dollars_to_percent(yes_ask)
        yes_bid_pct = dollars_to_percent(yes_bid)
        no_ask_pct = dollars_to_percent(no_ask)
        no_bid_pct = dollars_to_percent(no_bid)
        last_price_pct = dollars_to_percent(last_price)

        edge = None
        decision = "WATCHLIST"

        if yes_ask_pct is not None and ai_prob is not None:
            edge = round(ai_prob - yes_ask_pct, 2)

            if edge >= EDGE_THRESHOLD:
                decision = "BUY_YES"
            elif edge <= -EDGE_THRESHOLD:
                decision = "BUY_NO"
            else:
                decision = "SKIP"

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ticker,
            title,
            status,
            parsed.get("city"),
            parsed.get("date"),
            parsed.get("market_type"),
            parsed.get("comparison"),
            parsed.get("threshold_low"),
            parsed.get("threshold_high"),
            pred_temp,
            ai_prob,
            yes_ask_pct,
            yes_bid_pct,
            no_ask_pct,
            no_bid_pct,
            last_price_pct,
            edge,
            decision
        ]

        rows.append(row)

        print("=" * 90)
        print("TITLE          :", title)
        print("AI PROB YES    :", ai_prob)
        print("YES ASK %      :", yes_ask_pct)
        print("YES BID %      :", yes_bid_pct)
        print("NO ASK %       :", no_ask_pct)
        print("NO BID %       :", no_bid_pct)
        print("LAST PRICE %   :", last_price_pct)
        print("EDGE           :", edge)
        print("DECISION       :", decision)

    if rows:
        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"\nSaved {len(rows)} rows to {OUTPUT_FILE}")
    else:
        print("No active markets processed.")


if __name__ == "__main__":
    main()

