import csv
import os
from collections import defaultdict

INPUT_FILE = "data/kalshi_backtest_directional.csv"


def main():
    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    stats = defaultdict(lambda: {
        "total": 0,
        "signals": 0,
        "wins": 0,
        "losses": 0,
        "no_signal": 0
    })

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            comparison = (row.get("comparison") or "").strip()
            result = (row.get("result") or "").strip().upper()

            if not comparison:
                continue

            stats[comparison]["total"] += 1

            if result == "WIN":
                stats[comparison]["signals"] += 1
                stats[comparison]["wins"] += 1

            elif result == "LOSS":
                stats[comparison]["signals"] += 1
                stats[comparison]["losses"] += 1

            else:
                stats[comparison]["no_signal"] += 1

    print("=" * 80)
    print("BACKTEST BY MARKET TYPE")
    print("=" * 80)

    for comparison, s in stats.items():
        signals = s["signals"]
        wins = s["wins"]
        losses = s["losses"]
        total = s["total"]
        no_signal = s["no_signal"]

        accuracy = round((wins / signals) * 100, 2) if signals > 0 else 0.0

        print(f"TYPE        : {comparison}")
        print(f"Total       : {total}")
        print(f"Signals     : {signals}")
        print(f"Wins        : {wins}")
        print(f"Losses      : {losses}")
        print(f"No signal   : {no_signal}")
        print(f"Accuracy %  : {accuracy}")
        print("-" * 80)


if __name__ == "__main__":
    main()
