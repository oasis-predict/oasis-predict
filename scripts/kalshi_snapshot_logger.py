import csv
import os
from datetime import datetime

TRACKER_FILE = "data/kalshi_strategy_live_tracker.csv"
SNAPSHOT_FILE = "data/kalshi_performance_snapshots.csv"

INITIAL_BANKROLL = 1000.0


def safe_float(x):
    try:
        return float(x)
    except:
        return None


def get_risk_fraction(action, confidence_label):
    action = (action or "").strip().upper()
    confidence_label = (confidence_label or "").strip().upper()

    if action in ["BUY_YES_STRONG", "BUY_NO_STRONG"] and confidence_label == "HIGH":
        return 0.03

    if confidence_label == "HIGH":
        return 0.02

    if confidence_label == "MEDIUM":
        return 0.01

    return 0.005


def calculate_pnl(action, yes_price, outcome, stake):
    yes_price = safe_float(yes_price)

    if yes_price is None:
        return 0.0

    action = (action or "").strip().upper()
    outcome = (outcome or "").strip().upper()

    if action in ["BUY_YES", "BUY_YES_STRONG"]:
        if outcome == "YES":
            return stake * ((100 - yes_price) / 100)
        elif outcome == "NO":
            return -stake

    if action in ["BUY_NO", "BUY_NO_STRONG"]:
        no_price = 100 - yes_price
        if outcome == "NO":
            return stake * ((100 - no_price) / 100)
        elif outcome == "YES":
            return -stake

    return 0.0


def simulate_bankroll(rows):
    bankroll = INITIAL_BANKROLL

    for r in rows:
        outcome = (r.get("resolved_outcome") or "").strip().upper()
        if outcome not in ["YES", "NO"]:
            continue

        action = r.get("signal_action")
        confidence_label = r.get("confidence_label")
        yes_price = r.get("yes_ask_percent")

        risk_fraction = get_risk_fraction(action, confidence_label)
        stake = bankroll * risk_fraction

        pnl = calculate_pnl(action, yes_price, outcome, stake)
        bankroll += pnl

    return round(bankroll, 2)


def main():
    if not os.path.exists(TRACKER_FILE):
        print("Tracker file not found:", TRACKER_FILE)
        return

    rows = []
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    total = len(rows)
    wins = sum(1 for r in rows if (r.get("trade_result") or "").upper() == "WIN")
    losses = sum(1 for r in rows if (r.get("trade_result") or "").upper() == "LOSS")
    pending = sum(1 for r in rows if (r.get("trade_result") or "").upper() == "PENDING")

    decided = wins + losses
    win_rate = round((wins / decided) * 100, 2) if decided > 0 else 0.0

    pnl_values = [safe_float(r.get("pnl_percent")) for r in rows]
    pnl_values = [x for x in pnl_values if x is not None]
    total_pnl = round(sum(pnl_values), 2) if pnl_values else 0.0

    final_bankroll = simulate_bankroll(rows)
    bankroll_return = round((final_bankroll / INITIAL_BANKROLL - 1) * 100, 2)

    os.makedirs("data", exist_ok=True)
    file_exists = os.path.exists(SNAPSHOT_FILE)

    with open(SNAPSHOT_FILE, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp",
            "total_trades",
            "wins",
            "losses",
            "pending",
            "win_rate_percent",
            "total_pnl_percent",
            "final_bankroll",
            "bankroll_return_percent"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate_percent": win_rate,
            "total_pnl_percent": total_pnl,
            "final_bankroll": final_bankroll,
            "bankroll_return_percent": bankroll_return
        })

    print("=" * 80)
    print("PERFORMANCE SNAPSHOT SAVED")
    print("=" * 80)
    print("Total trades            :", total)
    print("Wins                    :", wins)
    print("Losses                  :", losses)
    print("Pending                 :", pending)
    print("Win rate %              :", win_rate)
    print("Total PnL %             :", total_pnl)
    print("Final bankroll          :", final_bankroll)
    print("Bankroll return %       :", bankroll_return)
    print(f"\nSaved snapshot to {SNAPSHOT_FILE}")


if __name__ == "__main__":
    main()
