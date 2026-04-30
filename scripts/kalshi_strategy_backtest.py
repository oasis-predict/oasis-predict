import csv
import os

INPUT_FILE = "data/kalshi_backtest_directional.csv"


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def strategy_a(row):
    comparison = (row.get("comparison") or "").strip()
    return comparison in ["between", "less_than"]


def strategy_b(row):
    comparison = (row.get("comparison") or "").strip()
    ai_prob = safe_float(row.get("ai_probability_yes"))

    if comparison in ["between", "less_than"]:
        return True

    if comparison == "greater_than" and ai_prob is not None and ai_prob >= 75.0:
        return True

    return False


def strategy_c(row):
    return True


def evaluate_strategy(rows, strategy_name, strategy_fn):
    filtered = [r for r in rows if strategy_fn(r)]

    wins = 0
    losses = 0
    no_signal = 0

    for r in filtered:
        result = (r.get("result") or "").strip().upper()

        if result == "WIN":
            wins += 1
        elif result == "LOSS":
            losses += 1
        else:
            no_signal += 1

    signals = wins + losses
    total = len(filtered)
    accuracy = round((wins / signals) * 100, 2) if signals > 0 else 0.0

    return {
        "strategy": strategy_name,
        "total_markets": total,
        "signals": signals,
        "wins": wins,
        "losses": losses,
        "no_signal": no_signal,
        "accuracy": accuracy
    }


def main():
    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    rows = []

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    results = [
        evaluate_strategy(rows, "A_between_less_than", strategy_a),
        evaluate_strategy(rows, "B_between_less_than_plus_strict_greater", strategy_b),
        evaluate_strategy(rows, "C_all_markets", strategy_c),
    ]

    print("=" * 90)
    print("KALSHI STRATEGY BACKTEST COMPARISON")
    print("=" * 90)

    for r in results:
        print("Strategy     :", r["strategy"])
        print("Total markets:", r["total_markets"])
        print("Signals      :", r["signals"])
        print("Wins         :", r["wins"])
        print("Losses       :", r["losses"])
        print("No signal    :", r["no_signal"])
        print("Accuracy %   :", r["accuracy"])
        print("-" * 90)


if __name__ == "__main__":
    main()
