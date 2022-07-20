from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time

def save_file(name, data):
    """
    Here we save the data of a file by name specified of the arguments
    """
    columns = ["timestep", "latency", "carbon_emissions", "server_name", "server_utilization"]
    res = defaultdict(list)
    for i, t in enumerate(data):
        for e in t:
            res["timestep"].append(i)
            res["server_name"].append(e["server"]["name"])
            res["server_utilization"].append(e["server"]["utilization"])
            res["latency"].append(e["latency"])
            res["carbon_emissions"].append(e["carbon_emissions"])

    df = pd.DataFrame(data=res)
    df.to_csv(name + ".csv", index=False)

def load_file(name):
    """
    Here we load a file specified by name specified by the arguments
    """
    df = pd.read_csv(name)
    n = len(df["timestep"].unique())

    data = [[] for _ in range(n)]
    for index, row in df.iterrows():
        obj = {}
        obj["latency"] = row["latency"]
        obj["carbon_emissions"] = row["carbon_emissions"]
        obj["server"] = {
            "name": row["server_name"],
            "utilization": row["server_utilization"]
        }
        timestep = int(row["timestep"])
        data[timestep].append(obj)

    return data

def load(name, resample=True, resample_metric="W"):
    df = pd.read_csv(name)
    if resample:
        df.datetime = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S.%f")
        df.set_index(["datetime"], inplace=True)
        df = df.resample(resample_metric)
    return df
