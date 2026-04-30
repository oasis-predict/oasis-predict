import csv
import os
from statistics import mean

INPUT_FILE = "data/kalshi_decisions.csv"


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def main():

    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("No decision data found.")
        return

    total = len(rows)

    buy_yes = [r for r in rows if r.get("decision") == "BUY_YES"]
    buy_no = [r for r in rows if r.get("decision") == "BUY_NO"]
    skip = [r for r in rows if r.get("decision") == "SKIP"]
    watchlist = [r for r in rows if r.get("decision") == "WATCHLIST"]

    edges = []
    ai_probs = []

    for r in rows:
        edge = safe_float(r.get("edge")) or safe_float(r.get("edge_vs_yes_ask"))
        ai_prob = safe_float(r.get("ai_probability_yes"))

        if edge is not None:
            edges.append(edge)

        if ai_prob is not None:
            ai_probs.append(ai_prob)

    print("=" * 80)
    print("KALSHI AGENT PERFORMANCE SUMMARY")
    print("=" * 80)
    print("Total rows        :", total)
    print("BUY_YES           :", len(buy_yes))
    print("BUY_NO            :", len(buy_no))
    print("SKIP              :", len(skip))
    print("WATCHLIST         :", len(watchlist))

    if edges:
        print("Average edge      :", round(mean(edges), 2))
        print("Max edge          :", round(max(edges), 2))
        print("Min edge          :", round(min(edges), 2))
    else:
        print("Average edge      : N/A")

    if ai_probs:
        print("Average AI prob   :", round(mean(ai_probs), 2))
        print("Max AI prob       :", round(max(ai_probs), 2))
        print("Min AI prob       :", round(min(ai_probs), 2))
    else:
        print("Average AI prob   : N/A")

import csv
import os
from statistics import mean

INPUT_FILE = "data/kalshi_decisions.csv"


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def main():

    if not os.path.exists(INPUT_FILE):
        print("File not found:", INPUT_FILE)
        return

    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        print("No decision data found.")
        return

    total = len(rows)

    buy_yes = [r for r in rows if r.get("decision") == "BUY_YES"]
    buy_no = [r for r in rows if r.get("decision") == "BUY_NO"]
    skip = [r for r in rows if r.get("decision") == "SKIP"]
    watchlist = [r for r in rows if r.get("decision") == "WATCHLIST"]

    edges = []
    ai_probs = []

    for r in rows:
        edge = safe_float(r.get("edge")) or safe_float(r.get("edge_vs_yes_ask"))
        ai_prob = safe_float(r.get("ai_probability_yes"))

        if edge is not None:
            edges.append(edge)

        if ai_prob is not None:
            ai_probs.append(ai_prob)

    print("=" * 80)
    print("KALSHI AGENT PERFORMANCE SUMMARY")
    print("=" * 80)
    print("Total rows        :", total)
    print("BUY_YES           :", len(buy_yes))
    print("BUY_NO            :", len(buy_no))
    print("SKIP              :", len(skip))
    print("WATCHLIST         :", len(watchlist))

    if edges:
        print("Average edge      :", round(mean(edges), 2))
        print("Max edge          :", round(max(edges), 2))
        print("Min edge          :", round(min(edges), 2))
    else:
        print("Average edge      : N/A")

    if ai_probs:
        print("Average AI prob   :", round(mean(ai_probs), 2))
        print("Max AI prob       :", round(max(ai_probs), 2))
        print("Min AI prob       :", round(min(ai_probs), 2))
    else:
        print("Average AI prob   : N/A")

    print("=" * 80)
    print("TOP SIGNALS")
    print("=" * 80)

    scored = []
    for r in rows:
        edge = safe_float(r.get("edge")) or safe_float(r.get("edge_vs_yes_ask"))
        if edge is not None:
            scored.append((abs(edge), r, edge))

    scored.sort(reverse=True, key=lambda x: x[0])

    for _, r, real_edge in scored[:10]:
        print("Ticker    :", r.get("ticker"))
        print("Decision  :", r.get("decision"))
        print("AI Prob   :", r.get("ai_probability_yes"))
        print("Yes Ask   :", r.get("yes_ask_percent"))
        print("Edge      :", round(real_edge, 2))
        print("Title     :", r.get("title"))
        print("-" * 80)


if __name__ == "__main__":
    main()
