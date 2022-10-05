import pandas as pd
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime, timezone, timedelta


def is_valid_file(file):
    return isfile(file)


DAYS = 6
YEAR = 2022

ROOT = "saved/akamai_data/akamai_sample_data/"
LOAD_PATH = join(ROOT, "ECORGeoLoad")
INFO_PATH = join(ROOT, "ECORInfo")
SAVE_PATH = "data/na/request"

STATES = {
    "Virginia": "VA",
    "California": "CA",
    "Texas": "TX",
    "Washington": "WA",
    "Ontario": "ON",
    "Iowa": "IA",
    "Arizona": "AZ",
    "Illinois": "IL",
    "Quebec": "QC",
    "Wyoming": "WY",
}
INVERSE_STATES = {v: k for k, v in STATES.items()}

dfs = {r: pd.DataFrame(columns=["timestamp", "datetime", *STATES.keys()]) for r in STATES.keys()}


load_files = [join(LOAD_PATH, f) for f in listdir(LOAD_PATH) if is_valid_file(join(LOAD_PATH, f))]

for load_path in load_files:
    info_path = join(INFO_PATH, f"{os.path.basename(load_path)}.clean")
    print(load_path)
    print(info_path)
    load_df = pd.read_csv(load_path, low_memory=False)
    info_df = pd.read_csv(info_path)

    info_df = info_df[info_df["b.continent"] == "North America"]
    info_df = info_df[info_df["b.state"].isin(STATES.values())]

    lookup = {row["a.ecor"]: INVERSE_STATES[row["b.state"]] for index, row in info_df.iterrows()}
    valid_ecor = info_df["a.ecor"].to_numpy()

    load_df["georegion"] = load_df["georegion"].apply(lambda x: x[3:-2])
    load_df = load_df[load_df["georegion"].isin(STATES.keys())]
    load_df = load_df[load_df["ecor"].isin(valid_ecor)]
    load_df["ecor"] = load_df["ecor"].apply(lambda x: lookup[x])
    load_df = load_df.rename(
        columns={"ecor": "from", "georegion": "to", "#query_time": "timestamp", "sum_hits": "requests"}
    )
    load_df = load_df[["timestamp", "from", "to", "requests"]]

    if len(load_df["timestamp"]) == 0:
        print("SKIPPED")
        continue
    timestamp = int(load_df["timestamp"].iloc[0])

    regions = {r: {s: 0 for s in STATES.keys()} for r in STATES.keys()}
    for index, row in load_df.iterrows():
        regions[row["from"]][row["to"]] += row["requests"]

    for key in dfs:
        new_df = pd.DataFrame(
            {"timestamp": timestamp, "datetime": datetime.fromtimestamp(timestamp), **regions[key]},
            index=[0],
        )
        dfs[key] = pd.concat([dfs[key], new_df], ignore_index=True)


def apply_group(x):
    date = x["datetime"].iloc[0]
    d = datetime.fromisoformat(date)
    t = d.replace(tzinfo=timezone.utc).timestamp()
    s = dict(x[STATES.keys()].sum())
    new_df = pd.DataFrame(
        {"timestamp": t, "datetime": date, **s},
        index=[0],
    )
    return new_df


for key in dfs:
    p = join(SAVE_PATH, f"{key}.csv")
    for i in range(DAYS):
        df = dfs[key].copy()
        df["datetime"] = df["datetime"].apply(
            lambda x: (x.replace(year=YEAR, minute=0, second=0) + timedelta(days=i)).isoformat()
        )
        df = df.groupby(["datetime"]).apply(apply_group)
        df = df.sort_values(by=["timestamp"])
        if i == 0:
            df.to_csv(p, index=False)
        else:
            df.to_csv(p, mode="a", header=False, index=False)
