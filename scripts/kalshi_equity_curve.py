import csv
import os
from datetime import datetime

import matplotlib.pyplot as plt

INPUT_FILE = "data/kalshi_performance_snapshots.csv"
OUTPUT_FILE = "data/kalshi_equity_curve.png"


def safe_float(x):
    try:
        return float(x)
    except:
        return None


def parse_timestamp(x):
    try:
        return datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
    except:
        return None


def main():
    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    timestamps = []
    bankrolls = []
    returns = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ts = parse_timestamp(row.get("timestamp"))
            bankroll = safe_float(row.get("final_bankroll"))
            ret = safe_float(row.get("bankroll_return_percent"))

            if ts is None or bankroll is None or ret is None:
                continue

            timestamps.append(ts)
            bankrolls.append(bankroll)
            returns.append(ret)

    if not timestamps:
        print("No valid snapshot data found.")
        return

    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, bankrolls, marker="o", label="Final Bankroll")
    plt.plot(timestamps, returns, marker="x", label="Return %")

    plt.title("Kalshi Strategy Performance Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Value")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    plt.savefig(OUTPUT_FILE, dpi=150)
    print("Chart saved to", OUTPUT_FILE)


if __name__ == "__main__":
    main()
