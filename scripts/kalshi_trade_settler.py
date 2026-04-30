import csv
import os

TRADE_LOG_FILE = "data/executed_trades.csv"


def load_trades():
    if not os.path.exists(TRADE_LOG_FILE):
        print("File not found:", TRADE_LOG_FILE)
        return []

    with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_trades(rows):
    if not rows:
        print("No trades to save.")
        return

    with open(TRADE_LOG_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = rows[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def find_trade(rows, ticker):
    ticker = ticker.strip().upper()
    for row in rows:
        if (row.get("ticker") or "").strip().upper() == ticker:
            return row
    return None


def normalize_settlement_status(status):
    status = (status or "").strip().upper()

    if status in ["WON", "WIN"]:
        return "WON"
    if status in ["LOST", "LOSS"]:
        return "LOST"
    if status in ["SETTLED"]:
        return "SETTLED"

    return None


def main():
    rows = load_trades()
    if not rows:
        print("No trade log found or file is empty.")
        return

    ticker = input("Ticker to settle: ").strip()
    row = find_trade(rows, ticker)

    if row is None:
        print("Ticker not found in executed_trades.csv")
        return

    print("-" * 80)
    print("FOUND TRADE")
    print("-" * 80)
    print("Ticker           :", row.get("ticker"))
    print("Title            :", row.get("title"))
    print("Signal Action    :", row.get("signal_action"))
    print("Execution Status :", row.get("execution_status"))
    print("Settlement Status:", row.get("settlement_status"))
    print("Realized PnL USD :", row.get("realized_pnl_usd"))
    print("-" * 80)

    settlement_status = normalize_settlement_status(
        input("Settlement status (WON / LOST / SETTLED): ")
    )

    if settlement_status is None:
        print("Invalid settlement status.")
        return

    realized_pnl = input("Realized PnL USD (example: 12.50 or -7.25): ").strip()

    try:
        realized_pnl_val = float(realized_pnl)
    except:
        print("Invalid PnL value.")
        return

    real_fill_price = input("Real fill price % (optional, press Enter to skip): ").strip()
    notes = input("Notes (optional): ").strip()

    row["execution_status"] = "EXECUTED"
    row["settlement_status"] = settlement_status
    row["realized_pnl_usd"] = str(round(realized_pnl_val, 2))

    if real_fill_price:
        try:
            row["real_fill_price_percent"] = str(round(float(real_fill_price), 2))
        except:
            print("Invalid fill price ignored.")

    if notes:
        row["notes"] = notes

    save_trades(rows)

    print("=" * 80)
    print("TRADE SETTLED")
    print("=" * 80)
    print("Ticker            :", row.get("ticker"))
    print("Settlement Status :", row.get("settlement_status"))
    print("Realized PnL USD  :", row.get("realized_pnl_usd"))
    print(f"Saved to {TRADE_LOG_FILE}")


if __name__ == "__main__":
    main()
