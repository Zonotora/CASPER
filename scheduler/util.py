from collections import defaultdict
from datetime import datetime, timezone
from grpc import server
import pandas as pd
import os

from scheduler.constants import REGION_NAMES, REGION_OFFSETS


def save_file(plot):
    """
    Here we save the data of a file by name specified of the arguments
    """
    df_inner = plot.build_df()
    date = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    if not os.path.exists("saved"):
        os.makedirs("saved")
    df_inner.to_csv(f"saved/{date}_inner.csv", index=False)


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
        obj["server"] = {"name": row["server_name"], "utilization": row["server_utilization"]}
        timestep = int(row["timestep"])
        data[timestep].append(obj)

    return data


def load_electricity_map_with_resample(path, metric="W"):
    """
    Loads electricity map data with resample to smooth out graph
    """
    df = pd.read_csv(path)
    df.datetime = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S.%f")
    df.set_index(["datetime"], inplace=True)
    df = df.resample(metric)
    return df


def load_carbon_intensity(path, offset, date="2021-01-01"):
    """
    Loads carbon intensity for a Region taking time offset to california into account
    for a certain date.
    """
    df = pd.read_csv(path)
    start_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    timestamp = int(start_date.timestamp())
    index = df.index[df["timestamp"] == timestamp]

    assert len(index) > 0, f"Date [{start_date}] does not exist in electricity map data"

    start = index[0] + offset
    # TODO: Consider more than just 24 hours ahead
    end = start + 24 + 24

    assert end < len(df), "The selected interval overflows the electricity map data"

    # TODO: Consider whether avg or take everything
    df = df["carbon_intensity_avg"].iloc[start:end].reset_index(drop=True)

    return df


def load_request_rate(path, offset, date="2021-01-01"):
    """
    Loads request rate data for a region and returns its data.
    """
    df = pd.read_csv(path)
    start_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    timestamp = int(start_date.timestamp())
    index = df.index[df["timestamp"] == timestamp]

    assert len(index) > 0, f"Date [{start_date}] does not exist in request rate data"

    start = index[0] + offset
    # TODO: Consider more than just 24 hours ahead
    end = start + 24 + 24
    assert end < len(df), "The selected interval overflows the reqeust rate data"

    df = df["requests"].iloc[start:end].reset_index(drop=True)

    return df

def ui(timestep, request_per_region, servers, servers_per_regions_list):
    print(f"______________________________________ \n TIMESTEP: {timestep}")
    print("Requests per region:")
    [print(f"{REGION_NAMES[i]} - {request[0]}") for i, request in enumerate(request_per_region)]
    print(" \n SERVERS PER REGION: \n")
    [print(f"{REGION_NAMES[i]} - {servers_per_region}") for i, servers_per_region in enumerate(servers_per_regions_list)]
    print("\n Server objects in ServerManager: ")
    print(servers)
    print("______________________________________")
