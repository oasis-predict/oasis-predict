import pandas as pd

# charger dataset historique
df = pd.read_csv("data/weather_history_multi.csv")

# convertir timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

df = df.sort_values(["city","timestamp"])

# créer target future (t+24h)
df["temp_future"] = df.groupby("city")["temp"].shift(-8)

# supprimer lignes vides
df = df.dropna()

# features
df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day

df.to_csv("data/weather_timeseries_dataset.csv", index=False)

print("Dataset time-series créé")
