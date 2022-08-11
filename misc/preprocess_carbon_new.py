from datetime import datetime, timezone, timedelta
from operator import index
from posixpath import relpath
import pandas as pd
import pytz
import os
import json
import numpy as np
import time

provider = "azure"
path = "api\\azure\\"
na_regions = ["Arizona", "California","Illinois", "Iowa", "Ontario", "Texas", "Virginia", "Washington", "Wyoming"
, "Quebec"]

#Regional info
df = pd.read_json(path + "cloud_regions.full.json")
df = df[df["provider"] == provider]
df = df[df["name"].isin(na_regions)]

#Read carbon info
dfs = [pd.read_csv(path + "us\\" + provider + "-" + region_code + "-" + "series.csv", index_col = False) for region_code in df["code"]]

for df, region in zip(dfs, na_regions):
    print(region)
    print(df["zone_carbon_intensity_avg"])
    df = df[[
        #"timestamp",
        "zone_datetime", "zone_carbon_intensity_avg"]]
    df.columns = [
        #"timestamp",
        "datetime", "carbon_intensity_avg"]
    if df.shape[0]% 2 != 0:
        first_row = pd.DataFrame([df.iloc[0]])
        df = pd.concat([first_row, df], ignore_index= True)

    #carbon_df = carbon_df.groupby(np.arange(len(carbon_df))//2).mean()

    df.loc[:,"datetime"] = pd.to_datetime(df["datetime"])

    #df["carbon_intensity_avg"] = carbon_df
    df.resample('H', on= "datetime").mean()

    df.to_csv(f"api\\north_america\\{region}.csv", index=False)
