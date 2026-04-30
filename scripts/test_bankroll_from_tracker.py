import csv

file = "data/kalshi_strategy_live_tracker.csv"

bankroll = 1000  # ton point de départ

for row in csv.reader(open(file)):
    if len(row) < 8:
        continue

    result = row[7]

    if result == "WIN":
        bankroll += 20   # approximation
    elif result == "LOSS":
        bankroll -= 10   # approximation

print("Estimated bankroll:", bankroll)
