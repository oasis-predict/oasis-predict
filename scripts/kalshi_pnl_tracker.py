import csv
import os

DECISIONS_FILE = "data/kalshi_decisions.csv"
PNL_FILE = "data/kalshi_pnl.csv"


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def outcome_matches(decision, outcome):
    decision = (decision or "").upper()
    outcome = (outcome or "").upper()

    if decision == "BUY_YES" and outcome == "YES":
        return True

    if decision == "BUY_NO" and outcome == "NO":
        return True

    return False


def calculate_pnl(decision, yes_ask, outcome):
    if yes_ask is None:
        return None

    decision = (decision or "").upper()
    outcome = (outcome or "").upper()

    # BUY YES
    if decision == "BUY_YES":
        if outcome == "YES":
            return round(100 - yes_ask, 2)
        elif outcome == "NO":
            return round(-yes_ask, 2)

    # BUY NO
    if decision == "BUY_NO":
        cost = 100 - yes_ask
        if outcome == "NO":
            return round(100 - cost, 2)
        elif outcome == "YES":
            return round(-cost, 2)

    return None


def create_initial_file():
    if not os.path.exists(DECISIONS_FILE):
        print("Decisions file not found")
        return

    rows = []

    with open(DECISIONS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("decision") in ["BUY_YES", "BUY_NO"]:

                edge = r.get("edge") or r.get("edge_vs_yes_ask")

                rows.append({
                    "ticker": r.get("ticker"),
                    "title": r.get("title"),
                    "decision": r.get("decision"),
                    "yes_ask_percent": r.get("yes_ask_percent"),
                    "ai_probability_yes": r.get("ai_probability_yes"),
                    "edge": edge,
                    "resolved_outcome": "",
                    "trade_result": "PENDING",
                    "pnl_percent": ""
                })

    with open(PNL_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created PnL file with {len(rows)} trades")


def update_pnl():
    if not os.path.exists(PNL_FILE):
        print("PnL file not found → creating...")
        create_initial_file()
        return

    rows = []

    with open(PNL_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:

            decision = r.get("decision")
            yes_ask = safe_float(r.get("yes_ask_percent"))
            outcome = (r.get("resolved_outcome") or "").upper()

            if outcome in ["YES", "NO"]:
                win = outcome_matches(decision, outcome)
                r["trade_result"] = "WIN" if win else "LOSS"
                r["pnl_percent"] = calculate_pnl(decision, yes_ask, outcome)
            else:
                r["trade_result"] = "PENDING"
                r["pnl_percent"] = ""

            rows.append(r)

    with open(PNL_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("PnL file updated")

    # SUMMARY
    print("=" * 80)
    print("PNL SUMMARY")
    print("=" * 80)

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

    print("Total trades :", total)
    print("Wins         :", wins)
    print("Losses       :", losses)
    print("Pending      :", pending)
    print("Total PnL %  :", total_pnl)


def main():
    if not os.path.exists(PNL_FILE):
        create_initial_file()
    else:
        update_pnl()


if __name__ == "__main__":
    main()
