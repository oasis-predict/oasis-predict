import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import joblib
import requests
import config
import pandas as pd
from datetime import datetime

model = joblib.load("models/weather_future_24h.pkl")

for city in config.CITIES:

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.API_KEY}&units=metric"
    data = requests.get(url).json()

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind = data["wind"]["speed"]

    now = datetime.now()

    X = pd.DataFrame([[humidity,pressure,wind,now.hour,now.day]],
    columns=["humidity","pressure","wind","hour","day"])

    pred = model.predict(X)[0]

    print("City:", city)
    print("Predicted temp in 24h:", round(pred,2),"°C")
    print("--------------------")
