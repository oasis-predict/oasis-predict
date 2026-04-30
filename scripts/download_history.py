import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import config
import csv

API_KEY = config.API_KEY
CITY = "New York,US"

url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric"

data = requests.get(url).json()

csv_file = "data/weather_history.csv"

with open(csv_file,"w",newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "timestamp",
        "temp",
        "humidity",
        "pressure",
        "wind"
    ])

for item in data["list"]:

    timestamp = item["dt"]

    temp = item["main"]["temp"]
    humidity = item["main"]["humidity"]
    pressure = item["main"]["pressure"]
    wind = item["wind"]["speed"]

    with open(csv_file,"a",newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            timestamp,
            temp,
            humidity,
            pressure,
            wind
        ])

print("Weather history dataset created")
