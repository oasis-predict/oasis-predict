import csv
import os
from collections import defaultdict

TRADE_LOG_FILE = "data/executed_trades.csv"


def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


def extract_city(title):
    if not title:
        return "UNKNOWN"

    title = title.upper()

    if "LOS ANGELES" in title or "LA" in title:
        return "LA"
    if "NYC" in title or "NEW YORK" in title:
        return "NYC"
    if "CHICAGO" in title:
        return "CHICAGO"

    return "OTHER"


def load_trades():
    if not os.path.exists(TRADE_LOG_FILE):
        print("File not found:", TRADE_LOG_FILE)
        return []

    with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def update_stats(stats, key, pnl, won):
    stats[key]["count"] += 1
    stats[key]["pnl"] += pnl
    if won:
        stats[key]["wins"] += 1


def print_section(title, stats):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    for key, data in sorted(stats.items()):
        count = data["count"]
        wins = data["wins"]
        pnl = data["pnl"]

        win_rate = (wins / count * 100) if count > 0 else 0

        print(f"{key:15} | Trades: {count:3} | Win%: {win_rate:6.2f} | PnL: {pnl:8.2f}")


def main():
    rows = load_trades()
    if not rows:
        print("No trades found.")
        return

    by_action = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})
    by_comparison = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})
    by_city = defaultdict(lambda: {"count": 0, "wins": 0, "pnl": 0.0})

    total_trades = 0
    total_wins = 0
    total_pnl = 0.0

    for row in rows:
        status = (row.get("settlement_status") or "").strip().upper()

        if status not in ["WON", "LOST"]:
            continue

        pnl = safe_float(row.get("realized_pnl_usd"))
        action = (row.get("signal_action") or "").strip().upper()
        comparison = (row.get("comparison") or "").strip().lower()
        city = extract_city(row.get("title"))

        won = status == "WON"

        update_stats(by_action, action, pnl, won)
        update_stats(by_comparison, comparison, pnl, won)
        update_stats(by_city, city, pnl, won)

        total_trades += 1
        total_pnl += pnl
        if won:
            total_wins += 1

    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0

    print("=" * 80)
    print("POST-TRADE AUDIT")
    print("=" * 80)
    print(f"Total trades : {total_trades}")
    print(f"Win rate     : {win_rate:.2f}%")
    print(f"Total PnL    : {total_pnl:.2f}$")

    print_section("BY ACTION", by_action)
    print_section("BY COMPARISON", by_comparison)
    print_section("BY CITY", by_city)


if __name__ == "__main__":
    main()
