import pandas as pd
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime, timezone


def is_valid_file(file):
    return isfile(file) and "csv" in file

PATH = "api/carbon"

files = [f"{PATH}/{f}" for f in listdir(PATH) if is_valid_file(join(PATH, f))]

df = None
for file in files:
    name = os.path.splitext(os.path.basename(file))[0]
    name = name.replace("azure-", "")
    name = name.replace("-series", "")
    new_df = pd.read_csv(file)[["zone_datetime", "zone_carbon_intensity_avg"]]
    new_df = new_df.rename(columns={"zone_carbon_intensity_avg": name, "zone_datetime": "datetime"})
    new_df["datetime"] = pd.to_datetime(new_df["datetime"])
    new_df = new_df.resample('H', on= "datetime").mean()
    if df is None:
        df = new_df
    else:
        df = df.merge(new_df, on='datetime', how="outer")

df = df.interpolate(method ='linear', axis = 0, direction = "forward")
df.insert(0, "datetime", df.index)
df.insert(0, "timestamp", df.index)
df['datetime'] = df['datetime'].apply(lambda d: d.isoformat())
df['timestamp'] = df['timestamp'].apply(lambda d: d.replace(tzinfo=timezone.utc).timestamp())
df.to_csv(f"api/carbon_intensity.csv", index=False)
