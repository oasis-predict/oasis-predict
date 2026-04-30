import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import csv
import requests
import config

API_KEY = config.API_KEY
CITIES = config.CITIES

csv_file = "data/weather_history_multi.csv"

with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "city",
        "timestamp",
        "temp",
        "humidity",
        "pressure",
        "wind"
    ])

for city in CITIES:
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url, timeout=20)
    data = response.json()

    if "list" not in data:
        print(f"Erreur API pour {city}: {data}")
        continue

    for item in data["list"]:
        timestamp = item["dt"]
        temp = item["main"]["temp"]
        humidity = item["main"]["humidity"]
        pressure = item["main"]["pressure"]
        wind = item["wind"]["speed"]

        with open(csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                city,
                timestamp,
                temp,
                humidity,
                pressure,
                wind
            ])

    print(f"Historique téléchargé pour {city}")

print("Dataset multi-villes créé")
