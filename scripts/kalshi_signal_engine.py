import csv
import os
import requests
from datetime import datetime

from parse_kalshi_weather_market import parse_kalshi_question
from kalshi_probability_engine import estimate_probability_from_question
from weather_consensus import get_city_weather_consensus

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/markets"
DETAIL_URL = "https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}"

SERIES_LIST = [
    "KXHIGHLAX",   # Los Angeles
    "KXHIGHNY",    # New York
    "KXHIGHCHI",   # Chicago
]

OUTPUT_FILE = "data/kalshi_signals.csv"

HEADERS = {
    "Accept": "application/json"
}


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def to_percent(x):
    if x is None:
        return None
    return round(x * 100, 2)


def get_market_detail(ticker):
    url = DETAIL_URL.format(ticker=ticker)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("market", {})


def compute_edge(ai_prob, yes_ask):
    if ai_prob is None or yes_ask is None:
        return None
    return round(ai_prob - yes_ask, 2)


def compute_confidence(parsed, prob_result, yes_ask, yes_bid, no_ask, no_bid, edge):
    score = 50

    ai_prob = prob_result.get("ai_probability_yes")
    std_dev = prob_result.get("std_dev")
    comparison = parsed.get("comparison")
    low = parsed.get("threshold_low")
    high = parsed.get("threshold_high")

    if edge is not None:
        abs_edge = abs(edge)

        if abs_edge >= 30:
            score += 25
        elif abs_edge >= 20:
            score += 18
        elif abs_edge >= 10:
            score += 10
        elif abs_edge >= 5:
            score += 3
        else:
            score -= 8

    if std_dev is not None:
        if std_dev <= 2.5:
            score += 12
        elif std_dev <= 4.0:
            score += 6
        elif std_dev <= 6.0:
            score += 1
        elif std_dev > 8.0:
            score -= 12
        elif std_dev > 6.0:
            score -= 6

    if comparison == "between":
        score += 4
        if low is not None and high is not None:
            width = high - low
            if width <= 1:
                score -= 4
            elif width <= 2:
                score -= 2

    elif comparison == "less_than":
        score += 3

    elif comparison == "greater_than":
        score += 0

    if ai_prob is not None:
        if ai_prob <= 10 or ai_prob >= 90:
            score += 12
        elif ai_prob <= 20 or ai_prob >= 80:
            score += 8
        elif 45 <= ai_prob <= 55:
            score -= 10

    quote_count = sum(v is not None for v in [yes_ask, yes_bid, no_ask, no_bid])
    if quote_count == 4:
        score += 8
    elif quote_count >= 2:
        score += 3
    else:
        score -= 5

    if yes_ask is not None:
        if yes_ask <= 5 or yes_ask >= 95:
            score += 5
        elif 40 <= yes_ask <= 60:
            score -= 5

    score = max(0, min(100, score))

    if score >= 75:
        label = "HIGH"
    elif score >= 55:
        label = "MEDIUM"
    else:
        label = "LOW"

    return score, label


def decide(parsed, edge, confidence, ai_prob):
    if edge is None or ai_prob is None:
        return "WATCHLIST"

    abs_edge = abs(edge)

    if abs_edge < 5:
        return "SKIP"

    if edge >= 20 and confidence >= 75:
        return "BUY_YES_STRONG"

    if edge <= -20 and confidence >= 75:
        return "BUY_NO_STRONG"

    if edge >= 8 and confidence >= 50:
        return "BUY_YES"

    if edge <= -8 and confidence >= 50:
        return "BUY_NO"

    if abs_edge >= 5 and confidence >= 45:
        if edge > 0:
            return "BUY_YES"
        return "BUY_NO"

    return "SKIP"


CITY_CONSENSUS_MAP = {
    "Los Angeles": "LA",
    "New York": "NYC",
    "Chicago": "Chicago",
}


def normalize_consensus_city(city_name):
    return CITY_CONSENSUS_MAP.get(city_name)


def normalize_target_date(date_text):
    if not date_text:
        return None

    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def save_signals(rows):
    os.makedirs("data", exist_ok=True)

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
            "std_dev",
            "openmeteo_temp_f",
            "noaa_temp_f",
            "nasa_monitor_temp_f",
            "consensus_temp_f",
            "consensus_spread_f",
            "consensus_ok",
            "yes_allowed",
            "range_center",
            "distance_to_consensus",
            "ai_probability_yes",
            "yes_ask_percent",
            "yes_bid_percent",
            "no_ask_percent",
            "no_bid_percent",
            "edge",
            "confidence_score",
            "confidence_label",
            "signal_action"
        ])
        writer.writerows(rows)


def main():
    markets = []
    saved_rows = []

    for series in SERIES_LIST:
        params = {"series_ticker": series, "limit": 100}
        try:
            r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            print(f"Status for {series}:", r.status_code)
            r.raise_for_status()
            data = r.json().get("markets", [])
            markets.extend(data)
        except Exception as e:
            print(f"Error fetching {series}: {e}")

    for m in markets:
        title = m.get("title")
        ticker = m.get("ticker")
        status = str(m.get("status", "")).lower()

        if not title or not ticker:
            continue

        if status not in ["active", "initialized"]:
            continue

        parsed = parse_kalshi_question(title)
        prob = estimate_probability_from_question(title)

        ai_prob = prob.get("ai_probability_yes")
        std_dev = prob.get("std_dev")
        pred_temp = prob.get("predicted_temp")

        try:
            detail = get_market_detail(ticker)
        except Exception as e:
            print(f"Error fetching detail for {ticker}: {e}")
            continue

        yes_ask = to_percent(safe_float(detail.get("yes_ask_dollars")))
        yes_bid = to_percent(safe_float(detail.get("yes_bid_dollars")))
        no_ask = to_percent(safe_float(detail.get("no_ask_dollars")))
        no_bid = to_percent(safe_float(detail.get("no_bid_dollars")))

        edge = compute_edge(ai_prob, yes_ask)

        conf_score, conf_label = compute_confidence(
            parsed,
            prob,
            yes_ask,
            yes_bid,
            no_ask,
            no_bid,
            edge
        )

        action = decide(parsed, edge, conf_score, ai_prob)

        consensus_city = normalize_consensus_city(parsed.get("city"))
        target_date = normalize_target_date(parsed.get("date"))
        openmeteo_temp = None
        noaa_temp = None
        nasa_monitor_temp = None
        consensus_temp = None
        consensus_spread = None
        consensus_ok = None
        yes_allowed = None

        if consensus_city and target_date:
            try:
                cons = get_city_weather_consensus(consensus_city, target_date)
                openmeteo_temp = cons.get("openmeteo_temp")
                noaa_temp = cons.get("noaa_temp")
                nasa_monitor_temp = cons.get("nasa_monitor_temp")
                consensus_ok = cons.get("consensus_ok")
                yes_allowed = cons.get("yes_allowed")
                consensus_temp = cons.get("consensus_temp")
                consensus_spread = cons.get("spread")

                if action.startswith("BUY_YES") and consensus_spread is not None and not yes_allowed:
                    print(
                        f"[CONSENSUS BLOCK] {ticker} | city={consensus_city} | action={action} | yes_allowed={yes_allowed} | spread={consensus_spread}"
                    )
                    action = "SKIP"

                if consensus_spread is not None and not consensus_ok and parsed.get("comparison") == "less_than":
                    print(
                        f"[CONSENSUS LESS_THAN BLOCK] {ticker} | city={consensus_city} | action={action} | spread={consensus_spread}"
                    )
                    action = "SKIP"

                elif consensus_spread is not None and not consensus_ok and action.startswith("BUY_NO"):
                    print(
                        f"[CONSENSUS DOWNGRADE] {ticker} | city={consensus_city} | action={action} | spread={consensus_spread}"
                    )
                    conf_label = "LOW"

                if consensus_spread is None:
                    print(
                        f"[CONSENSUS INCOMPLETE] {ticker} | city={consensus_city} | openmeteo={openmeteo_temp} | noaa={noaa_temp} | nasa={nasa_monitor_temp}"
                    )
            except Exception as e:
                print(f"[CONSENSUS ERROR] {ticker} | city={consensus_city} | date={target_date} | error={e}")

        # ==============================
        # RANGE DISTANCE FILTER (ANTI-TRAP)
        # ==============================
        range_center = None
        distance_to_consensus = None

        low = parsed.get("threshold_low")
        high = parsed.get("threshold_high")

        try:
            if parsed.get("comparison") == "between" and low is not None and high is not None:
                low = float(low)
                high = float(high)
                range_center = (low + high) / 2.0

                if consensus_temp is not None:
                    distance_to_consensus = abs(range_center - consensus_temp)

                    if distance_to_consensus < 2.0:
                        print(
                            f"[RANGE FILTER BLOCK] {ticker} | center={range_center} | consensus={consensus_temp} | distance={distance_to_consensus}"
                        )
                        action = "SKIP"
        except Exception as e:
            print(f"[RANGE FILTER ERROR] {ticker} | error={e}")

        print("=" * 80)
        print("TITLE     :", title)
        print("TYPE      :", parsed.get("comparison"))
        print("AI PROB   :", ai_prob)
        print("YES ASK   :", yes_ask)
        print("EDGE      :", edge)
        print("STD DEV   :", std_dev)
        print("CONSENSUS :", openmeteo_temp, noaa_temp, nasa_monitor_temp, consensus_temp, consensus_spread, consensus_ok, yes_allowed)
        print("CONF      :", conf_score, conf_label)
        print("ACTION    :", action)

        if action in ["BUY_YES", "BUY_NO", "BUY_YES_STRONG", "BUY_NO_STRONG"]:
            saved_rows.append([
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
                std_dev,
                openmeteo_temp,
                noaa_temp,
                nasa_monitor_temp,
                consensus_temp,
                consensus_spread,
                consensus_ok,
                yes_allowed,
                round(range_center, 2) if range_center is not None else '',
                round(distance_to_consensus, 2) if distance_to_consensus is not None else '',
                ai_prob,
                yes_ask,
                yes_bid,
                no_ask,
                no_bid,
                edge,
                conf_score,
                conf_label,
                action
            ])

    save_signals(saved_rows)
    print(f"\nSaved {len(saved_rows)} signal(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
