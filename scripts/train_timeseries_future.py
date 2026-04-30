import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

df = pd.read_csv("data/weather_timeseries_dataset.csv")

X = df[["humidity","pressure","wind","hour","day"]]
y = df["temp_future"]

model = RandomForestRegressor(n_estimators=200)

model.fit(X,y)

joblib.dump(model,"models/weather_future_24h.pkl")

print("Modèle t+24h entraîné")
