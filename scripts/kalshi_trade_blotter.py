import csv
import os
import re
from datetime import datetime

INPUT_FILE = "data/kalshi_trade_sheet.csv"

MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
    "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
}


def safe_float(x):
    try:
        return float(x)
    except:
        return None


def extract_market_date_from_ticker(ticker):
    if not ticker:
        return None

    match = re.search(r"-(\d{2})([A-Z]{3})(\d{2})-", ticker)
    if not match:
        return None

    yy, mon_str, dd = match.groups()
    year = 2000 + int(yy)
    month = MONTH_MAP.get(mon_str.upper())
    day = int(dd)

    if not month:
        return None

    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def market_day_offset(ticker, today=None):
    market_dt = extract_market_date_from_ticker(ticker)
    if market_dt is None:
        return None

    if today is None:
        today = datetime.now()

    return (market_dt.date() - today.date()).days


def is_los_angeles_trade(row):
    title = (row.get("title") or "").lower()
    ticker = (row.get("ticker") or "").upper()
    return ("los angeles" in title) or ("**high temp in la**" in title) or ("KXHIGHLAX" in ticker)


def classify_bucket(row):
    priority = (row.get("priority") or "").upper()
    comparison = (row.get("comparison") or "").lower()
    action = (row.get("signal_action") or "").upper()
    edge_val = abs(safe_float(row.get("edge")) or 0.0)
    day_offset = market_day_offset(row.get("ticker") or "")
    is_la = is_los_angeles_trade(row)

    # PRIMARY = la shortlist la plus propre
    if (
        priority == "TOP"
        and comparison == "between"
        and action in ["BUY_NO", "BUY_NO_STRONG"]
        and day_offset == 1
        and not is_la
        and edge_val >= 12
    ):
        return "PRIMARY"

    # SECONDARY = tout le reste encore valable
    return "SECONDARY"


def sort_key(row):
    bucket_rank = {"PRIMARY": 0, "SECONDARY": 1}
    priority_rank = {"TOP": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    edge_val = abs(safe_float(row.get("edge")) or 0.0)
    day_offset = market_day_offset(row.get("ticker") or "")

    if day_offset == 1:
        day_rank = 0
    elif day_offset == 0:
        day_rank = 1
    else:
        day_rank = 2

    return (
        bucket_rank.get(row.get("bucket"), 9),
        priority_rank.get((row.get("priority") or "").upper(), 9),
        day_rank,
        -edge_val
    )


def main():
    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["bucket"] = classify_bucket(row)
            rows.append(row)

    if not rows:
        print("No trades found.")
        return

    rows.sort(key=sort_key)

    print("=" * 100)
    print("FINAL TRADE BLOTTER")
    print("=" * 100)

    current_bucket = None

    for row in rows:
        if row["bucket"] != current_bucket:
            current_bucket = row["bucket"]
            print()
            print("#" * 100)
            print(f"{current_bucket} TRADES")
            print("#" * 100)

        print("Ticker              :", row.get("ticker"))
        print("Bucket              :", row.get("bucket"))
        print("Priority            :", row.get("priority"))
        print("Action              :", row.get("signal_action"))
        print("Comparison          :", row.get("comparison"))
        print("AI Prob YES         :", row.get("ai_probability_yes"))
        print("YES Price %         :", row.get("yes_price_percent"))
        print("NO Price %          :", row.get("no_price_percent"))
        print("Edge                :", row.get("edge"))
        print("Recommended Stake $ :", row.get("recommended_stake_usd"))
        print("Estimated Cost $    :", row.get("estimated_trade_cost_usd"))
        print("Title               :", row.get("title"))
        print("-" * 100)


if __name__ == "__main__":
    main()
