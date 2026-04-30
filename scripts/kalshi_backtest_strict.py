import csv
import os

INPUT_FILE = "data/kalshi_backtest_directional.csv"
OUTPUT_FILE = "data/kalshi_backtest_strict.csv"

YES_THRESHOLD = 65.0
NO_THRESHOLD = 35.0
ALLOWED_COMPARISONS = {"greater_than", "less_than"}


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def strict_direction(ai_prob):
    if ai_prob is None:
        return None

    if ai_prob >= YES_THRESHOLD:
        return "YES"

    if ai_prob <= NO_THRESHOLD:
        return "NO"

    return None


def main():
    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    rows_out = []

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            comparison = (row.get("comparison") or "").strip()
            if comparison not in ALLOWED_COMPARISONS:
                continue

            ai_prob = safe_float(row.get("ai_probability_yes"))
            resolved_outcome = (row.get("resolved_outcome") or "").strip().upper()

            if resolved_outcome not in ["YES", "NO"]:
                continue

            predicted_direction = strict_direction(ai_prob)
            if predicted_direction is None:
                result = "NO_SIGNAL"
            elif predicted_direction == resolved_outcome:
                result = "WIN"
            else:
                result = "LOSS"

            rows_out.append({
                "ticker": row.get("ticker"),
                "title": row.get("title"),
                "comparison": comparison,
                "ai_probability_yes": ai_prob,
                "predicted_direction": predicted_direction,
                "resolved_outcome": resolved_outcome,
                "result": result,
                "source": row.get("source"),
                "predicted_temp_f": row.get("predicted_temp_f"),
                "std_dev": row.get("std_dev")
            })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "ticker",
            "title",
            "comparison",
            "ai_probability_yes",
            "predicted_direction",
            "resolved_outcome",
            "result",
            "source",
            "predicted_temp_f",
            "std_dev"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    total = len(rows_out)
    wins = sum(1 for r in rows_out if r["result"] == "WIN")
    losses = sum(1 for r in rows_out if r["result"] == "LOSS")
    no_signal = sum(1 for r in rows_out if r["result"] == "NO_SIGNAL")
    decided = wins + losses
    accuracy = round((wins / decided) * 100, 2) if decided > 0 else 0.0

    print("=" * 80)
    print("STRICT DIRECTIONAL BACKTEST")
    print("=" * 80)
    print("Total markets :", total)
    print("Signals       :", decided)
    print("Wins          :", wins)
    print("Losses        :", losses)
    print("No signal     :", no_signal)
    print("Accuracy %    :", accuracy)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
