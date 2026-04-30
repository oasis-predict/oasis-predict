import joblib
import requests
import config
import pandas as pd
from datetime import datetime

model = joblib.load("models/weather_model.pkl")

for city in config.CITIES:

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.API_KEY}&units=metric"
    data = requests.get(url).json()

    temp_real = data["main"]["temp"]

    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    wind_speed = data["wind"]["speed"]
    clouds = data["clouds"]["all"]
    visibility = data.get("visibility",0)
    rain = data.get("rain",{}).get("1h",0)

    now = datetime.now()

    city_code = hash(city)%1000

    X = pd.DataFrame([[city_code,humidity,pressure,wind_speed,clouds,visibility,rain,now.hour,now.day]],
    columns=["city","humidity","pressure","wind_speed","clouds","visibility","rain","hour","day"])

    pred = model.predict(X)[0]

    print(city)
    print("AI prediction:",round(pred,2))
    print("Real temp:",temp_real)
    print("Error:",abs(pred-temp_real))
    print("-----------")
