import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

df = pd.read_csv("data/weather_history_multi.csv")

df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day

cities = df["city"].unique()

os.makedirs("models/cities", exist_ok=True)

for city in cities:
    city_df = df[df["city"] == city].copy()

    if len(city_df) < 5:
        print(f"Pas assez de données pour {city}")
        continue

    X = city_df[["humidity", "pressure", "wind", "hour", "day"]]
    y = city_df["temp"]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    safe_city = city.replace(",", "_").replace(" ", "_")
    model_path = f"models/cities/{safe_city}_model.pkl"
    joblib.dump(model, model_path)

    print(f"Modèle entraîné pour {city} -> {model_path}")

print("Tous les modèles par ville sont prêts")
