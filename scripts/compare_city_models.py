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

    real_temp = data["main"]["temp"]
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]

    now = datetime.now()

    X = pd.DataFrame(
        [[humidity, pressure, wind, now.hour, now.day]],
        columns=["humidity", "pressure", "wind", "hour", "day"]
    )

    ai_temp = model.predict(X)[0]
    error = abs(ai_temp - real_temp)

    print("City:", city)
    print("AI temp:", round(ai_temp, 2), "°C")
    print("API temp:", real_temp, "°C")
    print("Gap:", round(error, 2), "°C")
    print("----------------------")
