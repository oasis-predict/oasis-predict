import csv
import os

SIGNALS_FILE = "data/kalshi_signals.csv"
TRACK_FILE = "data/kalshi_strategy_live_tracker.csv"


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def create_tracker_file():
    if not os.path.exists(SIGNALS_FILE):
        print("Signals file not found:", SIGNALS_FILE)
        return False

    rows = []

    with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            rows.append({
                "timestamp": r.get("timestamp"),
                "ticker": r.get("ticker"),
                "title": r.get("title"),
                "comparison": r.get("comparison"),
                "signal_action": r.get("signal_action"),
                "yes_ask_percent": r.get("yes_ask_percent"),
                "ai_probability_yes": r.get("ai_probability_yes"),
                "edge": r.get("edge"),
                "confidence_score": r.get("confidence_score"),
                "confidence_label": r.get("confidence_label"),
                "resolved_outcome": "",
                "trade_result": "PENDING",
                "pnl_percent": ""
            })

    with open(TRACK_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp",
            "ticker",
            "title",
            "comparison",
            "signal_action",
            "yes_ask_percent",
            "ai_probability_yes",
            "edge",
            "confidence_score",
            "confidence_label",
            "resolved_outcome",
            "trade_result",
            "pnl_percent"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Tracker created with {len(rows)} signal(s).")
    return True


def outcome_matches(action, outcome):
    action = (action or "").upper()
    outcome = (outcome or "").upper()

    if action in ["BUY_YES", "BUY_YES_STRONG"] and outcome == "YES":
        return True

    if action in ["BUY_NO", "BUY_NO_STRONG"] and outcome == "NO":
        return True

    return False


def calculate_pnl(action, yes_price, outcome):
    action = (action or "").upper()
    outcome = (outcome or "").upper()
    yes_price = safe_float(yes_price)

    if yes_price is None:
        return None

    if action in ["BUY_YES", "BUY_YES_STRONG"]:
        if outcome == "YES":
            return round(100 - yes_price, 2)
        else:
            return round(-yes_price, 2)

    if action in ["BUY_NO", "BUY_NO_STRONG"]:
        no_price = 100 - yes_price
        if outcome == "NO":
            return round(100 - no_price, 2)
        else:
            return round(-no_price, 2)

    return None


def update_tracker():
    if not os.path.exists(TRACK_FILE):
        print("Tracker file not found. Creating...")
        create_tracker_file()
        return

    rows = []

    with open(TRACK_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            outcome = (r.get("resolved_outcome") or "").upper()
            action = r.get("signal_action")
            price = r.get("yes_ask_percent")

            if outcome in ["YES", "NO"]:
                win = outcome_matches(action, outcome)
                r["trade_result"] = "WIN" if win else "LOSS"
                pnl = calculate_pnl(action, price, outcome)
                r["pnl_percent"] = pnl
            else:
                r["trade_result"] = "PENDING"
                r["pnl_percent"] = ""

            rows.append(r)

    with open(TRACK_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp",
            "ticker",
            "title",
            "comparison",
            "signal_action",
            "yes_ask_percent",
            "ai_probability_yes",
            "edge",
            "confidence_score",
            "confidence_label",
            "resolved_outcome",
            "trade_result",
            "pnl_percent"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = len(rows)
    wins = sum(1 for r in rows if r["trade_result"] == "WIN")
    losses = sum(1 for r in rows if r["trade_result"] == "LOSS")
    pending = sum(1 for r in rows if r["trade_result"] == "PENDING")

    pnl_values = [
        safe_float(r["pnl_percent"])
        for r in rows
        if safe_float(r["pnl_percent"]) is not None
    ]

    total_pnl = round(sum(pnl_values), 2) if pnl_values else 0.0

    print("=" * 80)
    print("STRATEGY LIVE TRACKER")
    print("=" * 80)
    print("Total   :", total)
    print("Wins    :", wins)
    print("Losses  :", losses)
    print("Pending :", pending)
    print("PnL %   :", total_pnl)


def main():
    if not os.path.exists(TRACK_FILE):
        create_tracker_file()
    else:
        update_tracker()


if __name__ == "__main__":
    main()
