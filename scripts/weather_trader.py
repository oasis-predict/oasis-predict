import joblib
import requests
import config
import pandas as pd
from datetime import datetime

model = joblib.load("models/rain_model.pkl")

for city in config.CITIES:

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.API_KEY}&units=metric"
    data = requests.get(url).json()

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility",0)

    now = datetime.now()

    city_code = hash(city)%1000

    X = pd.DataFrame([[city_code,humidity,pressure,wind_speed,clouds,visibility,now.hour,now.day]],
    columns=["city","humidity","pressure","wind_speed","clouds","visibility","hour","day"])

    prob = model.predict_proba(X)[0][1]*100

    if prob > 70:
        print(city,"High rain probability -> possible weather trade")

    print(city,"Rain probability:",round(prob,2),"%")
    print("----------")
