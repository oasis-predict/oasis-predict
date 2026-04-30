import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

df = pd.read_csv("data/weather_data.csv")

df["timestamp"] = pd.to_datetime(df["timestamp"])
df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day

# pluie = 1 si rain > 0 sinon 0
df["rain_label"] = (df["rain"] > 0).astype(int)

# IMPORTANT: pas de colonne city
X = df[
    [
        "humidity",
        "pressure",
        "wind_speed",
        "clouds",
        "visibility",
        "hour",
        "day"
    ]
]

y = df["rain_label"]

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X, y)

joblib.dump(model, "models/rain_model.pkl")

print("Rain prediction model trained")
