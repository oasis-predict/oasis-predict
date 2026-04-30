import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import joblib
import pandas as pd
import requests
import config
from datetime import datetime, timedelta

model = joblib.load("models/weather_model.pkl")

API_KEY = config.API_KEY
CITIES = config.CITIES

for city in CITIES:

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    data = requests.get(url).json()

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility",0)
    rain = data.get("rain",{}).get("1h",0)

    city_code = hash(city) % 1000

    for hours in [3,6,12]:

        future = datetime.now() + timedelta(hours=hours)

        X = pd.DataFrame([[city_code,humidity,pressure,wind_speed,clouds,visibility,rain,future.hour,future.day]],
        columns=["city","humidity","pressure","wind_speed","clouds","visibility","rain","hour","day"])

        pred = model.predict(X)[0]

        print(city,"Forecast",hours,"h:",round(pred,2),"°C")

    print("--------------")
