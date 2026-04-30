import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import config
import joblib
import pandas as pd
from datetime import datetime

# modèles
rain_model = joblib.load("models/rain_model.pkl")
temp_model = joblib.load("models/weather_future_24h.pkl")

API_KEY = config.API_KEY
CITIES = config.CITIES

# seuils de décision
RAIN_BUY_THRESHOLD = 70
RAIN_SELL_THRESHOLD = 30

for city in CITIES:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url, timeout=20)
    data = response.json()

    if "main" not in data:
        print(f"Erreur API pour {city}: {data}")
        print("----------------------")
        continue

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility", 0)

    now = datetime.now()

    # features pluie
    X_rain = pd.DataFrame(
        [[humidity, pressure, wind_speed, clouds, visibility, now.hour, now.day]],
        columns=[
            "humidity",
            "pressure",
            "wind_speed",
            "clouds",
            "visibility",
            "hour",
            "day"
        ]
    )

    # features température future
    X_temp = pd.DataFrame(
        [[humidity, pressure, wind_speed, now.hour, now.day]],
        columns=[
            "humidity",
            "pressure",
            "wind",
            "hour",
            "day"
        ]
    )

    rain_probability = rain_model.predict_proba(X_rain)[0][1] * 100
    temp_24h = temp_model.predict(X_temp)[0]

    # logique décisionnelle simple
    if rain_probability >= RAIN_BUY_THRESHOLD:
        decision = "BUY RAIN"
    elif rain_probability <= RAIN_SELL_THRESHOLD:
        decision = "SELL RAIN / BUY NO-RAIN"
    else:
        decision = "SKIP"

    print("City:", city)
    print("Rain probability:", round(rain_probability, 2), "%")
    print("Predicted temp in 24h:", round(temp_24h, 2), "°C")
    print("Decision:", decision)
    print("----------------------")
