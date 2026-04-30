import csv
import os

SIGNALS_FILE = "data/kalshi_signals.csv"
PNL_FILE = "data/kalshi_signal_pnl.csv"


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def outcome_matches(action, outcome):
    action = (action or "").upper()
    outcome = (outcome or "").upper()

    if action in ["BUY_YES", "BUY_YES_STRONG"] and outcome == "YES":
        return True

    if action in ["BUY_NO", "BUY_NO_STRONG"] and outcome == "NO":
        return True

    return False


def calculate_pnl(action, yes_ask, outcome):
    if yes_ask is None:
        return None

    action = (action or "").upper()
    outcome = (outcome or "").upper()

    # BUY YES
    if action in ["BUY_YES", "BUY_YES_STRONG"]:
        if outcome == "YES":
            return round(100 - yes_ask, 2)
        elif outcome == "NO":
            return round(-yes_ask, 2)

    # BUY NO
    if action in ["BUY_NO", "BUY_NO_STRONG"]:
        cost = 100 - yes_ask
        if outcome == "NO":
            return round(100 - cost, 2)
        elif outcome == "YES":
            return round(-cost, 2)

    return None


def create_file():
    if not os.path.exists(SIGNALS_FILE):
        print("Signals file not found")
        return

    rows = []

    with open(SIGNALS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            rows.append({
                "ticker": r.get("ticker"),
                "title": r.get("title"),
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

    with open(PNL_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "ticker",
            "title",
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

    print("PnL file created")


def update_pnl():
    if not os.path.exists(PNL_FILE):
        create_file()
        return

    rows = []

    with open(PNL_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            action = r.get("signal_action")
            yes_ask = safe_float(r.get("yes_ask_percent"))
            outcome = (r.get("resolved_outcome") or "").upper()

            if outcome in ["YES", "NO"]:
                win = outcome_matches(action, outcome)
                r["trade_result"] = "WIN" if win else "LOSS"
                pnl = calculate_pnl(action, yes_ask, outcome)
                r["pnl_percent"] = pnl
            else:
                r["trade_result"] = "PENDING"
                r["pnl_percent"] = ""

            rows.append(r)

    with open(PNL_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "ticker",
            "title",
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

    print("=" * 60)
    print("SIGNAL PNL SUMMARY")
    print("=" * 60)

    total = len(rows)
    wins = sum(1 for r in rows if r["trade_result"] == "WIN")
    losses = sum(1 for r in rows if r["trade_result"] == "LOSS")
    pending = sum(1 for r in rows if r["trade_result"] == "PENDING")

    pnl_values = [
        safe_float(r["pnl_percent"])
        for r in rows
        if safe_float(r["pnl_percent"]) is not None
    ]

    total_pnl = round(sum(pnl_values), 2) if pnl_values else 0

    print("Total   :", total)
    print("Wins    :", wins)
    print("Losses  :", losses)
    print("Pending :", pending)
    print("PnL %   :", total_pnl)


def main():
    if not os.path.exists(PNL_FILE):
        create_file()
    else:
        update_pnl()


if __name__ == "__main__":
    main()
