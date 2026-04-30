import csv
import os
import requests

from parse_kalshi_weather_market import parse_kalshi_question
from kalshi_probability_engine import estimate_probability_from_question

BASE_LIST_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
BASE_DETAIL_URL = "https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"

SERIES_TICKER = "KXHIGHLAX"
OUTPUT_FILE = "data/kalshi_backtest_directional.csv"

headers = {
    "Accept": "application/json",
    "User-Agent": "weather-ai-agent/1.0"
}

BUY_YES_THRESHOLD = 55.0
BUY_NO_THRESHOLD = 45.0


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


def resolve_market_outcome(detail):
    result = (detail.get("result") or "").strip().upper()
    if result in ["YES", "NO"]:
        return result
    return None


def directional_decision(ai_prob):
    if ai_prob is None:
        return None
    if ai_prob >= BUY_YES_THRESHOLD:
        return "YES"
    if ai_prob <= BUY_NO_THRESHOLD:
        return "NO"
    return None


def outcome_is_correct(predicted_direction, resolved_outcome):
    if predicted_direction is None or resolved_outcome is None:
        return None
    return predicted_direction == resolved_outcome


def main():
    os.makedirs("data", exist_ok=True)

    params = {
        "series_ticker": SERIES_TICKER,
        "limit": 300
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

        if status not in ["finalized", "settled", "closed", "resolved"]:
            continue

        parsed = parse_kalshi_question(title)
        prob_result = estimate_probability_from_question(title)
        ai_prob = prob_result.get("ai_probability_yes")
        pred_temp = prob_result.get("predicted_temp")
        std_dev = prob_result.get("std_dev")
        source = prob_result.get("source")

        detail = fetch_market_detail(ticker)
        resolved_outcome = resolve_market_outcome(detail)

        yes_ask_pct = dollars_to_percent(safe_float(detail.get("yes_ask_dollars")))
        yes_bid_pct = dollars_to_percent(safe_float(detail.get("yes_bid_dollars")))
        no_ask_pct = dollars_to_percent(safe_float(detail.get("no_ask_dollars")))
        no_bid_pct = dollars_to_percent(safe_float(detail.get("no_bid_dollars")))
        last_price_pct = dollars_to_percent(safe_float(detail.get("last_price_dollars")))

        predicted_direction = directional_decision(ai_prob)
        correct = outcome_is_correct(predicted_direction, resolved_outcome)

        if correct is True:
            result_label = "WIN"
        elif correct is False:
            result_label = "LOSS"
        else:
            result_label = "NO_SIGNAL"

        row = {
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
            "source": source,
            "ai_probability_yes": ai_prob,
            "predicted_direction": predicted_direction,
            "resolved_outcome": resolved_outcome,
            "yes_ask_percent": yes_ask_pct,
            "yes_bid_percent": yes_bid_pct,
            "no_ask_percent": no_ask_pct,
            "no_bid_percent": no_bid_pct,
            "last_price_percent": last_price_pct,
            "result": result_label
        }

        rows.append(row)

    fieldnames = [
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
        "source",
        "ai_probability_yes",
        "predicted_direction",
        "resolved_outcome",
        "yes_ask_percent",
        "yes_bid_percent",
        "no_ask_percent",
        "no_bid_percent",
        "last_price_percent",
        "result"
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    wins = sum(1 for r in rows if r["result"] == "WIN")
    losses = sum(1 for r in rows if r["result"] == "LOSS")
    no_signal = sum(1 for r in rows if r["result"] == "NO_SIGNAL")
    decided = wins + losses
    accuracy = round((wins / decided) * 100, 2) if decided > 0 else 0.0

    print("=" * 90)
    print("DIRECTIONAL BACKTEST SUMMARY")
    print("=" * 90)
    print("Total markets :", total)
    print("Signals       :", decided)
    print("Wins          :", wins)
    print("Losses        :", losses)
    print("No signal     :", no_signal)
    print("Accuracy %    :", accuracy)
    print(f"\nSaved {len(rows)} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
