import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import joblib
import requests
import config
import pandas as pd
from datetime import datetime, timedelta

# charger modèle time-series
model = joblib.load("models/weather_timeseries.pkl")

API_KEY = config.API_KEY
CITIES = config.CITIES

for city in CITIES:

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    data = requests.get(url).json()

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]

    for hours in [24, 48]:

        future = datetime.now() + timedelta(hours=hours)

        X = pd.DataFrame(
            [[humidity, pressure, wind, future.hour, future.day]],
            columns=["humidity", "pressure", "wind", "hour", "day"]
        )

        prediction = model.predict(X)[0]

        print("City:", city)
        print("Forecast", hours, "hours:", round(prediction,2), "°C")
        print("-------------------")
