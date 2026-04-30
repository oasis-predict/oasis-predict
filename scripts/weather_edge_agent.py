import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import config
import joblib
import pandas as pd
from datetime import datetime

rain_model = joblib.load("models/rain_model.pkl")

API_KEY = config.API_KEY
CITIES = config.CITIES

# ⚠️ simulation marché (remplacera Polymarket plus tard)
market_probabilities = {
    "New York,US": 60,
    "Seattle,US": 75,
    "Chicago,US": 50,
    "Dallas,US": 30,
    "Tokyo,JP": 40,
    "Toronto,CA": 55,
    "Singapore,SG": 65,
    "London,GB": 70,
    "Seoul,KR": 45,
    "Paris,FR": 50
}

EDGE_THRESHOLD = 10

for city in CITIES:

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    data = requests.get(url).json()

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility", 0)

    now = datetime.now()

    X = pd.DataFrame(
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

    ai_prob = rain_model.predict_proba(X)[0][1] * 100

    market_prob = market_probabilities.get(city, 50)

    edge = ai_prob - market_prob

    print("City:", city)
    print("AI probability:", round(ai_prob,2), "%")
    print("Market probability:", market_prob, "%")
    print("EDGE:", round(edge,2), "%")

    if edge > EDGE_THRESHOLD:
        print("Signal: BUY RAIN")
    elif edge < -EDGE_THRESHOLD:
        print("Signal: BUY NO RAIN")
    else:
        print("No strong edge")

    print("---------------------")
