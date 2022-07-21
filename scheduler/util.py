from collections import defaultdict
import pandas as pd
from datetime import datetime


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

def load_request_rate(path="data\de.out", date_start="2007-12-12"):
    '''
    Dates between 2007-12-09-19:00:00 and 2013-10-16-16:00:00
    Returns array on 24 hour basis
    Assumes dataset time is relative to california. Shift with TEX(+2),MIDATLANTIC(+6),MIDWEST(+2)
    '''
    date = datetime.strptime(date_start,"%Y-%m-%d")
    date = int(datetime.strftime(date, "%Y%m%d%H%M%S"))

    request_rate = pd.read_csv(path, delimiter=" ", usecols=[0, 2])
    request_rate.columns = ["Dates", "Requests"]

    if date not in set(request_rate["Dates"]):
        raise Error("Date doesn't exist")

    cali_time_index = request_rate.index[request_rate["Dates"] == date][0]

    off_sets = {"CAL":0, "TEX":2, "MIDA":6,"MIDW":2}
    hours_of_data = 24
    request_regions = pd.DataFrame(columns = ["CAL", "TEX", "MIDA", "MIDW"])
    for region in request_regions:
        request_regions[region] = request_rate["Requests"].iloc[cali_time_index + off_sets[region]:
            cali_time_index + off_sets[region] + hours_of_data].reset_index(drop=True)

    return request_regions


