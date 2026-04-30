import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# charger dataset
df = pd.read_csv("data/weather_history.csv")

# convertir timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day

# variables pour le modèle
X = df[["humidity","pressure","wind","hour","day"]]

# ce qu'on veut prédire
y = df["temp"]

# modèle ML
model = RandomForestRegressor(n_estimators=200)

model.fit(X,y)

# sauvegarder modèle
joblib.dump(model,"models/weather_timeseries.pkl")

print("Time series model trained")
