import csv
import json
import os
from datetime import datetime

# fichiers
PARSED_MARKETS_FILE = "data/polymarket_weather_parsed.json"
PAPER_TRADES_FILE = "data/paper_trades.csv"

EDGE_THRESHOLD = 10.0


# ===== IA (version simple pour commencer) =====
def estimate_ai_probability(parsed_market):
    market_type = parsed_market.get("market_type")
    comparison = parsed_market.get("comparison")
    threshold = parsed_market.get("threshold")

    # heuristiques simples (temporaire)
    if market_type == "rain_event":
        return 55.0

    if market_type == "snow_event":
        return 35.0

    if market_type == "daily_high_temperature":
        return 50.0

    if market_type == "daily_low_temperature":
        return 50.0

    if market_type == "temperature_event":

        if comparison == "greater_than" and threshold is not None:
            if threshold <= 10:
                return 80.0
            elif threshold <= 18:
                return 60.0
            elif threshold <= 25:
                return 40.0
            else:
                return 20.0

        if comparison == "less_than" and threshold is not None:
            if threshold <= 0:
                return 20.0
            elif threshold <= 10:
                return 50.0
            else:
                return 70.0

        return 50.0

    return 50.0


# ===== décision =====
def decide_trade(ai_prob, market_yes_prob):
    edge = ai_prob - market_yes_prob

    if edge >= EDGE_THRESHOLD:
        return "BUY_YES", edge

    if edge <= -EDGE_THRESHOLD:
        return "BUY_NO", edge

    return "SKIP", edge


# ===== utilitaire =====
def safe_float(value):
    try:
        return float(value)
    except:
        return None


def ensure_csv_exists():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(PAPER_TRADES_FILE):
        with open(PAPER_TRADES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "market_id",
                "question",
                "city",
                "date",
                "market_type",
                "mode",
                "threshold",
                "market_yes_prob",
                "market_no_prob",
                "ai_prob",
                "edge",
                "decision",
                "status"
            ])


# ===== main =====
def main():

    ensure_csv_exists()

    if not os.path.exists(PARSED_MARKETS_FILE):
        print("❌ Parsed markets file not found")
        print("➡️ Lance d'abord : python scripts/polymarket_weather_pipeline.py")
        return

    with open(PARSED_MARKETS_FILE, "r", encoding="utf-8") as f:
        markets = json.load(f)

    if not markets:
        print("⚠️ Aucun marché météo disponible pour le moment")
        return

    print(f"Markets disponibles: {len(markets)}")
    print("=" * 80)

    rows = []

    for market in markets:

        parsed = market.get("parsed", {})
        outcomes = market.get("outcomes", [])
        prices = market.get("outcomePrices", [])

        question = market.get("question")
        market_id = market.get("id")

        city = parsed.get("city")
        date = parsed.get("date")
        market_type = parsed.get("market_type")
        threshold = parsed.get("threshold")
        mode = parsed.get("mode")

        # on traite seulement les marchés binaires
        if mode != "binary":
            continue

        if len(prices) < 2:
            continue

        market_yes_prob = safe_float(prices[0])
        market_no_prob = safe_float(prices[1])

        if market_yes_prob is None or market_no_prob is None:
            continue

        # convertir en %
        if market_yes_prob <= 1:
            market_yes_prob *= 100
            market_no_prob *= 100

        ai_prob = estimate_ai_probability(parsed)

        decision, edge = decide_trade(ai_prob, market_yes_prob)

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            market_id,
            question,
            city,
            date,
            market_type,
            mode,
            threshold,
            round(market_yes_prob, 2),
            round(market_no_prob, 2),
            round(ai_prob, 2),
            round(edge, 2),
            decision,
            "OPEN"
        ]

        rows.append(row)

        print("Question :", question)
        print("City     :", city)
        print("Date     :", date)
        print("Type     :", market_type)
        print("Market   :", round(market_yes_prob, 2), "%")
        print("AI       :", round(ai_prob, 2), "%")
        print("EDGE     :", round(edge, 2), "%")
        print("Decision :", decision)
        print("-" * 80)

    if rows:
        with open(PAPER_TRADES_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"✅ {len(rows)} trade(s) enregistrés")
    else:
        print("❌ Aucun trade généré")


if __name__ == "__main__":
    main()
