import csv
import os
import re

INPUT_FILE = "data/kalshi_trade_sheet.csv"
OUTPUT_FILE = "data/kalshi_strategy_live_tracker.csv"


def extract_city_from_ticker(ticker: str) -> str:
    ticker = ticker or ""
    if "LAX" in ticker:
        return "LA"
    if "NY" in ticker:
        return "NYC"
    if "CHI" in ticker:
        return "Chicago"
    if "DAL" in ticker:
        return "Dallas"
    if "HOU" in ticker:
        return "Houston"
    if "PHX" in ticker:
        return "Phoenix"
    return "Unknown"


def extract_market_date_from_ticker(ticker: str) -> str:
    """
    Example:
    KXHIGHNY-26MAR25-T58 -> 2026-03-25
    """
    m = re.search(r"-(\d{2})([A-Z]{3})(\d{2})-", ticker or "")
    if not m:
        return ""

    year_2 = m.group(1)
    mon_txt = m.group(2)
    day = m.group(3)

    month_map = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
        "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
        "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }

    month = month_map.get(mon_txt.upper(), "")
    if not month:
        return ""

    return f"20{year_2}-{month}-{day}"


def decision_from_action(action: str) -> str:
    action = (action or "").strip().upper()
    if action in ["BUY_YES", "BUY_YES_STRONG"]:
        return "YES"
    if action in ["BUY_NO", "BUY_NO_STRONG"]:
        return "NO"
    return ""


def load_existing_tickers(filepath: str) -> set:
    if not os.path.exists(filepath):
        return set()

    tickers = set()
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t = row.get("ticker")
            if t:
                tickers.add(t.strip())
    return tickers


def main():
    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    os.makedirs("data", exist_ok=True)

    existing_tickers = load_existing_tickers(OUTPUT_FILE)

    rows_to_add = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = (row.get("ticker") or "").strip()
            if not ticker:
                continue

            if ticker in existing_tickers:
                continue

            action = row.get("signal_action") or ""
            trade_decision = decision_from_action(action)
            market_date = extract_market_date_from_ticker(ticker)
            city = extract_city_from_ticker(ticker)

            rows_to_add.append({
                "date": market_date,
                "ticker": ticker,
                "title": row.get("title") or "",
                "comparison": row.get("comparison") or "",
                "signal_action": action,
                "city": city,
                "trade_decision": trade_decision,
                "trade_result": "PENDING",
            })

    file_exists = os.path.exists(OUTPUT_FILE)

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "date",
            "ticker",
            "title",
            "comparison",
            "signal_action",
            "city",
            "trade_decision",
            "trade_result",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.path.getsize(OUTPUT_FILE) == 0:
            writer.writeheader()

        for row in rows_to_add:
            writer.writerow(row)

    print("=" * 80)
    print("TRADES LOGGED TO STRATEGY TRACKER")
    print("=" * 80)
    print("New trades added :", len(rows_to_add))
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
