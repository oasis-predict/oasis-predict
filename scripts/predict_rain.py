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

model = joblib.load("models/rain_model.pkl")

for city in CITIES:

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility", 0)

    timestamp = datetime.now()

    hour = timestamp.hour
    day = timestamp.day

    city_code = hash(city) % 1000

    X = pd.DataFrame(
        [[city_code, humidity, pressure, wind_speed, clouds, visibility, hour, day]],
        columns=[
            "city",
            "humidity",
            "pressure",
            "wind_speed",
            "clouds",
            "visibility",
            "hour",
            "day"
        ]
    )

    proba = model.predict_proba(X)[0][1] * 100

print("City:", city)
print("Rain probability:", round(proba,2), "%")
print("---------------------")
