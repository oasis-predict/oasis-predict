import csv
import os

INPUT_FILE = "data/kalshi_backtest_directional.csv"
OUTPUT_FILE = "data/kalshi_filtered_pnl.csv"

EDGE_THRESHOLD = 5.0
CONFIDENCE_THRESHOLD = 10.0


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def compute_confidence(ai_prob):
    if ai_prob is None:
        return 0.0
    return abs(ai_prob - 50.0)


def compute_edge(ai_prob, market_price=50.0):
    if ai_prob is None:
        return None
    return round(ai_prob - market_price, 2)


def compute_pnl(predicted_direction, resolved_outcome, yes_price=50.0):
    if predicted_direction not in ["YES", "NO"]:
        return None

    if resolved_outcome not in ["YES", "NO"]:
        return None

    if predicted_direction == "YES":
        if resolved_outcome == "YES":
            return round(100 - yes_price, 2)
        else:
            return round(-yes_price, 2)

    if predicted_direction == "NO":
        no_price = 100 - yes_price
        if resolved_outcome == "NO":
            return round(100 - no_price, 2)
        else:
            return round(-no_price, 2)

    return None


def main():
    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    filtered_rows = []

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ai_prob = safe_float(row.get("ai_probability_yes"))
            predicted_direction = (row.get("predicted_direction") or "").strip().upper()
            resolved_outcome = (row.get("resolved_outcome") or "").strip().upper()

            if ai_prob is None:
                continue

            if predicted_direction not in ["YES", "NO"]:
                continue

            if resolved_outcome not in ["YES", "NO"]:
                continue

            edge = compute_edge(ai_prob, 50.0)
            if edge is None:
                continue

            confidence = compute_confidence(ai_prob)

            if abs(edge) < EDGE_THRESHOLD:
                continue

            if confidence < CONFIDENCE_THRESHOLD:
                continue

            pnl = compute_pnl(predicted_direction, resolved_outcome, 50.0)
            if pnl is None:
                continue

            result = "WIN" if pnl > 0 else "LOSS"

            filtered_rows.append({
                "ticker": row.get("ticker"),
                "title": row.get("title"),
                "ai_probability_yes": ai_prob,
                "predicted_direction": predicted_direction,
                "resolved_outcome": resolved_outcome,
                "edge": edge,
                "confidence": round(confidence, 2),
                "result": result,
                "pnl_percent": pnl
            })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "ticker",
            "title",
            "ai_probability_yes",
            "predicted_direction",
            "resolved_outcome",
            "edge",
            "confidence",
            "result",
            "pnl_percent"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_rows)

    total = len(filtered_rows)
    wins = sum(1 for r in filtered_rows if r["result"] == "WIN")
    losses = sum(1 for r in filtered_rows if r["result"] == "LOSS")
    total_pnl = round(sum(r["pnl_percent"] for r in filtered_rows), 2) if filtered_rows else 0.0
    avg_pnl = round(total_pnl / total, 2) if total > 0 else 0.0
    win_rate = round((wins / total) * 100, 2) if total > 0 else 0.0

    print("=" * 80)
    print("FILTERED DIRECTIONAL PNL BACKTEST")
    print("=" * 80)
    print("Trades       :", total)
    print("Wins         :", wins)
    print("Losses       :", losses)
    print("Win rate     :", win_rate)
    print("Total PnL %  :", total_pnl)
    print("Avg PnL/trade:", avg_pnl)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
