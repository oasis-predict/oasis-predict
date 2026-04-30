import csv
import os
from collections import defaultdict

FILE = "data/kalshi_strategy_live_tracker.csv"


def safe_float(x):
    try:
        return float(x)
    except:
        return None


def main():
    if not os.path.exists(FILE):
        print("File not found:", FILE)
        return

    rows = []

    with open(FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        print("No rows found.")
        return

    total = len(rows)
    wins = [r for r in rows if (r.get("trade_result") or "").upper() == "WIN"]
    losses = [r for r in rows if (r.get("trade_result") or "").upper() == "LOSS"]
    pending = [r for r in rows if (r.get("trade_result") or "").upper() == "PENDING"]

    decided = len(wins) + len(losses)
    win_rate = round((len(wins) / decided) * 100, 2) if decided > 0 else 0.0

    pnl_values = [safe_float(r.get("pnl_percent")) for r in rows]
    pnl_values = [x for x in pnl_values if x is not None]

    total_pnl = round(sum(pnl_values), 2) if pnl_values else 0.0

    win_pnls = [safe_float(r.get("pnl_percent")) for r in wins]
    win_pnls = [x for x in win_pnls if x is not None]

    loss_pnls = [safe_float(r.get("pnl_percent")) for r in losses]
    loss_pnls = [x for x in loss_pnls if x is not None]

    avg_gain = round(sum(win_pnls) / len(win_pnls), 2) if win_pnls else 0.0
    avg_loss = round(sum(loss_pnls) / len(loss_pnls), 2) if loss_pnls else 0.0

    best_trade = None
    worst_trade = None

    decided_rows = []
    for r in rows:
        pnl = safe_float(r.get("pnl_percent"))
        if pnl is not None:
            decided_rows.append((pnl, r))

    if decided_rows:
        best_trade = max(decided_rows, key=lambda x: x[0])
        worst_trade = min(decided_rows, key=lambda x: x[0])

    by_comparison = defaultdict(lambda: {"wins": 0, "losses": 0, "pending": 0, "pnl": 0.0})
    by_signal = defaultdict(lambda: {"wins": 0, "losses": 0, "pending": 0, "pnl": 0.0})

    for r in rows:
        comparison = r.get("comparison") or "UNKNOWN"
        signal = r.get("signal_action") or "UNKNOWN"
        result = (r.get("trade_result") or "").upper()
        pnl = safe_float(r.get("pnl_percent")) or 0.0

        if result == "WIN":
            by_comparison[comparison]["wins"] += 1
            by_signal[signal]["wins"] += 1
        elif result == "LOSS":
            by_comparison[comparison]["losses"] += 1
            by_signal[signal]["losses"] += 1
        else:
            by_comparison[comparison]["pending"] += 1
            by_signal[signal]["pending"] += 1

        by_comparison[comparison]["pnl"] += pnl
        by_signal[signal]["pnl"] += pnl

    print("=" * 90)
    print("KALSHI PERFORMANCE DASHBOARD")
    print("=" * 90)
    print("Total trades   :", total)
    print("Wins           :", len(wins))
    print("Losses         :", len(losses))
    print("Pending        :", len(pending))
    print("Win rate %     :", win_rate)
    print("Total PnL %    :", total_pnl)
    print("Average gain   :", avg_gain)
    print("Average loss   :", avg_loss)

    print("=" * 90)
    print("BEST TRADE")
    print("=" * 90)
    if best_trade:
        pnl, r = best_trade
        print("Ticker         :", r.get("ticker"))
        print("Title          :", r.get("title"))
        print("Signal         :", r.get("signal_action"))
        print("Comparison     :", r.get("comparison"))
        print("PnL %          :", pnl)
    else:
        print("No decided trade yet.")

    print("=" * 90)
    print("WORST TRADE")
    print("=" * 90)
    if worst_trade:
        pnl, r = worst_trade
        print("Ticker         :", r.get("ticker"))
        print("Title          :", r.get("title"))
        print("Signal         :", r.get("signal_action"))
        print("Comparison     :", r.get("comparison"))
        print("PnL %          :", pnl)
    else:
        print("No decided trade yet.")

    print("=" * 90)
    print("BREAKDOWN BY MARKET TYPE")
    print("=" * 90)
    for comparison, s in by_comparison.items():
        decided_count = s["wins"] + s["losses"]
        acc = round((s["wins"] / decided_count) * 100, 2) if decided_count > 0 else 0.0
        print("Type           :", comparison)
        print("Wins           :", s["wins"])
        print("Losses         :", s["losses"])
        print("Pending        :", s["pending"])
        print("Accuracy %     :", acc)
        print("PnL %          :", round(s["pnl"], 2))
        print("-" * 90)

    print("=" * 90)
    print("BREAKDOWN BY SIGNAL")
    print("=" * 90)
    for signal, s in by_signal.items():
        decided_count = s["wins"] + s["losses"]
        acc = round((s["wins"] / decided_count) * 100, 2) if decided_count > 0 else 0.0
        print("Signal         :", signal)
        print("Wins           :", s["wins"])
        print("Losses         :", s["losses"])
        print("Pending        :", s["pending"])
        print("Accuracy %     :", acc)
        print("PnL %          :", round(s["pnl"], 2))
        print("-" * 90)


if __name__ == "__main__":
    main()
