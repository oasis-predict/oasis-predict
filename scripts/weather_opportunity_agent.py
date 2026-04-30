import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import config
import joblib
import pandas as pd
from datetime import datetime

API_KEY = config.API_KEY
CITIES = config.CITIES

TEMP_EDGE_THRESHOLD = 2.5

for city in CITIES:
    safe_city = city.replace(",", "_").replace(" ", "_")
    model_path = f"models/cities/{safe_city}_model.pkl"

    if not os.path.exists(model_path):
        print(f"Modèle manquant pour {city}")
        print("----------------------")
        continue

    model = joblib.load(model_path)

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url, timeout=20)
    data = response.json()

    if "main" not in data:
        print(f"Erreur API pour {city}: {data}")
        print("----------------------")
        continue

    api_temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]

    now = datetime.now()

    X = pd.DataFrame(
        [[humidity, pressure, wind, now.hour, now.day]],
        columns=["humidity", "pressure", "wind", "hour", "day"]
    )

    ai_temp = model.predict(X)[0]
    edge = ai_temp - api_temp
    abs_edge = abs(edge)

    print("City:", city)
    print("AI temp:", round(ai_temp, 2), "°C")
    print("API temp:", api_temp, "°C")
    print("Edge:", round(edge, 2), "°C")

    if abs_edge >= TEMP_EDGE_THRESHOLD:
        if edge > 0:
            print("Signal: AI plus bullish than API")
        else:
            print("Signal: AI plus bearish than API")
        print("Opportunity detected")
    else:
        print("No strong opportunity")

    print("----------------------")
