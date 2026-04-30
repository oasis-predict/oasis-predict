import csv
from datetime import datetime, UTC

weather_file = "data/weather_history.csv"
trades_file = "kalshi_historical_test.csv"
output_file = "kalshi_historical_enriched.csv"


def c_to_f(temp_c):
    return (temp_c * 9 / 5) + 32


# 1) construire les max par jour depuis weather_history.csv
daily_highs = {}

with open(weather_file, "r", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        ts = int(row["timestamp"])
        temp_c = float(row["temp"])
        temp_f = c_to_f(temp_c)

        day = datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d")

        if day not in daily_highs:
            daily_highs[day] = temp_f
        else:
            daily_highs[day] = max(daily_highs[day], temp_f)

# 2) enrichir les trades
with open(trades_file, "r", newline="") as infile, open(output_file, "w", newline="") as outfile:
    reader = csv.DictReader(infile)

    base_fieldnames = reader.fieldnames[:] if reader.fieldnames else []
    fieldnames = base_fieldnames + ["real_temp"]

    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        # supprime les éventuelles colonnes en trop
        row.pop(None, None)

        trade_date = row.get("date", "").strip()
        temp = daily_highs.get(trade_date, "")

        row["real_temp"] = round(temp, 2) if temp != "" else ""

        clean_row = {key: row.get(key, "") for key in fieldnames}
        writer.writerow(clean_row)

print(f"Fichier créé : {output_file}")
