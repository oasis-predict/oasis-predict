import csv

input_file = "data/kalshi_strategy_live_tracker.csv"
output_file = "data/kalshi_tracker_clean.csv"

clean_rows = []

with open(input_file, "r") as f:
    for line in f:
        line = line.strip()

        # enlever les caractères parasites
        line = line.replace(">", "")
        
        # skip lignes vides ou cassées
        if not line or "KXHIGH" not in line:
            continue

        parts = line.split(",")

        if len(parts) < 8:
            continue

        row = {
            "date": parts[0],
            "ticker": parts[1],
            "question": parts[2],
            "comparison": parts[3],
            "signal": parts[4],
            "city": parts[5],
            "side": parts[6],
            "result": parts[7],
            "pnl": parts[8] if len(parts) > 8 else ""
        }

        clean_rows.append(row)

with open(output_file, "w", newline="") as f:
    fieldnames = ["date","ticker","question","comparison","signal","city","side","result","pnl"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for row in clean_rows:
        writer.writerow(row)

print(f"Clean file created: {output_file}")
