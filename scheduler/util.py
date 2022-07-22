from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import numpy as np
import os

from sqlalchemy import Integer

from scheduler.region import Region
from scheduler.constants import REGION_LOCATIONS, REGION_NAMES, REGION_OFFSETS


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
        obj["server"] = {"name": row["server_name"], "utilization": row["server_utilization"]}
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

def load_request_rate(path="data\de.out", date_start="2007-12-12", date_end="2007-12-13"):
    '''
    Dates between 2007-12-09-19:00:00 and 2013-10-16-16:00:00
    Returns array on 24 hour basis
    Assumes dataset time is relative to california. Shift with TEX(+2),MIDATLANTIC(+6),MIDWEST(+2)
    '''
    date_start_unformated = datetime.strptime(date_start, "%Y-%m-%d")
    date_start = int(datetime.strftime(date_start_unformated, "%Y%m%d%H%M%S"))

    date_end_unformated = datetime.strptime(date_end, "%Y-%m-%d")
    date_end = int(datetime.strftime(date_end_unformated, "%Y%m%d%H%M%S"))

    duration = (date_end_unformated - date_start_unformated)
    hours_of_data = duration.days * 24 + duration.seconds // 3600

    assert isinstance(hours_of_data, int)

    request_rate = pd.read_csv(path, delimiter=" ", usecols=[0, 2])
    request_rate.columns = ["Dates", "Requests"]

    if date_start not in set(request_rate["Dates"]):
        raise Exception("Date doesn't exist")

    cali_time_index = request_rate.index[request_rate["Dates"] == date_start][0]

    #off_sets = {"US-CAL-CISO":0, "US-TEX-ERCO":2, "US-MIDA-PJM":6,"US-MIDW-MISO":2}
    request_regions = pd.DataFrame(columns = [REGION_NAMES[i] for i in range(len(REGION_NAMES))])
    for region in request_regions:
        request_regions[region] = request_rate["Requests"].iloc[cali_time_index + REGION_OFFSETS[region]:
            cali_time_index + REGION_OFFSETS[region] + hours_of_data].reset_index(drop=True)

    print(request_regions)
    return request_regions


def load_region_data(d, resample=False, resample_metric="W"):
    '''

    '''
    data = {}
    regions_request_rate = load_request_rate()
    for file in os.listdir(d):
        if file.endswith(".csv"):
            path = os.path.join(d, file)
            name = os.path.basename(path)
            name, ext = os.path.splitext(name)
            region_data = {}
            region_data["data"] = load(path, resample=resample, resample_metric=resample_metric)
            location = REGION_LOCATIONS[name]
            region_request_rate = regions_request_rate[name]
            region_data["region"] = Region(name, location, region_request_rate, carbon_intensity)
            print(region_data["data"])
    print("US-CAL-CISO")
    return data
