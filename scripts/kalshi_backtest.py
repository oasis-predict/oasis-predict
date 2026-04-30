import csv
import os
import requests
from datetime import datetime

from parse_kalshi_weather_market import parse_kalshi_question
from kalshi_probability_engine import estimate_probability_from_question

BASE_LIST_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
BASE_DETAIL_URL = "https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"

SERIES_TICKER = "KXHIGHLAX"
OUTPUT_FILE = "data/kalshi_backtest.csv"

headers = {
    "Accept": "application/json",
    "User-Agent": "weather-ai-agent/1.0"
}

EDGE_THRESHOLD = 10.0


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


def decide_trade(ai_prob, yes_ask_pct):
    if ai_prob is None or yes_ask_pct is None:
        return None, None

    edge = round(ai_prob - yes_ask_pct, 2)

    if edge >= EDGE_THRESHOLD:
        return "BUY_YES", edge

    if edge <= -EDGE_THRESHOLD:
        return "BUY_NO", edge

    return "SKIP", edge


def resolve_market_outcome(detail):
    """
    Essaie d'inférer le résultat final.
    Si la donnée n'est pas exploitable, retourne None.
    """
    result = (detail.get("result") or "").strip().upper()

    if result in ["YES", "NO"]:
        return result

    # fallback possible si expiration_value ou autres champs sont vides
    return None


def calc_pnl(decision, yes_ask_pct, resolved_outcome):
    if decision not in ["BUY_YES", "BUY_NO"]:
        return None

    if yes_ask_pct is None or resolved_outcome not in ["YES", "NO"]:
        return None

    if decision == "BUY_YES":
        if resolved_outcome == "YES":
            return round(100 - yes_ask_pct, 2)
        else:
            return round(-yes_ask_pct, 2)

    if decision == "BUY_NO":
        no_cost = 100 - yes_ask_pct
        if resolved_outcome == "NO":
            return round(100 - no_cost, 2)
        else:
            return round(-no_cost, 2)

    return None


def main():
    os.makedirs("data", exist_ok=True)

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
        ticker = m.get("ticker")
        title = m.get("title")
        status = str(m.get("status", "")).lower()

        if not ticker or not title:
            continue

        # Backtest sur marchés passés / finalisés
        if status not in ["finalized", "settled", "closed", "resolved"]:
            continue

        parsed = parse_kalshi_question(title)
        prob_result = estimate_probability_from_question(title)

        ai_prob = prob_result.get("ai_probability_yes")
        pred_temp = prob_result.get("predicted_temp")
        std_dev = prob_result.get("std_dev")

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

        decision, edge = decide_trade(ai_prob, yes_ask_pct)
        resolved_outcome = resolve_market_outcome(detail)
        pnl = calc_pnl(decision, yes_ask_pct, resolved_outcome)

        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "title": title,
            "status": status,
            "city": parsed.get("city"),
            "date": parsed.get("date"),
            "comparison": parsed.get("comparison"),
            "threshold_low": parsed.get("threshold_low"),
            "threshold_high": parsed.get("threshold_high"),
            "predicted_temp_f": pred_temp,
            "std_dev": std_dev,
            "ai_probability_yes": ai_prob,
            "yes_ask_percent": yes_ask_pct,
            "yes_bid_percent": yes_bid_pct,
            "no_ask_percent": no_ask_pct,
            "no_bid_percent": no_bid_pct,
            "last_price_percent": last_price_pct,
            "edge": edge,
            "decision": decision,
            "resolved_outcome": resolved_outcome,
            "pnl_percent": pnl,
        }

        rows.append(row)

        print("=" * 90)
        print("TITLE            :", title)
        print("STATUS           :", status)
        print("AI PROB YES      :", ai_prob)
        print("YES ASK %        :", yes_ask_pct)
        print("EDGE             :", edge)
        print("DECISION         :", decision)
        print("RESOLVED OUTCOME :", resolved_outcome)
        print("PNL %            :", pnl)

    fieldnames = [
        "timestamp",
        "ticker",
        "title",
        "status",
        "city",
        "date",
        "comparison",
        "threshold_low",
        "threshold_high",
        "predicted_temp_f",
        "std_dev",
        "ai_probability_yes",
        "yes_ask_percent",
        "yes_bid_percent",
        "no_ask_percent",
        "no_bid_percent",
        "last_price_percent",
        "edge",
        "decision",
        "resolved_outcome",
        "pnl_percent",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} row(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
