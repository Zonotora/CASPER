from numpy import deprecate
from scheduler.constants import REGION_EUROPE, REGION_NORTH_AMERICA, REGION_ORIGINAL
from datetime import datetime, timezone
import pandas as pd
import os


def save_file(conf, plot):
    """Save the data of a file by name specified of the arguments. Usefull for misc visualisations.


    Args:
        conf: Runtime configurations to retrieve latency, max_servers, timesteps
        plot: Converts data from the plot object to dataframe
    """
    df = plot.build_df()
    date_created = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists("saved"):
        os.makedirs("saved")

    fingerprint = [
        str(conf.start_date) + "_",
        str(conf.type_scheduler),
        "_latency_",
        str(conf.latency),
        "_max_servers_",
        str(conf.max_servers),
        "_timesteps_",
        str(conf.timesteps),
    ]
    df.to_csv(f"saved/{date_created}_{''.join(fingerprint)}.csv", index=False)

@deprecate
def load_file(name):
    """Unused function to load saved file from save_file()

    Args:
        name: Name of file

    Returns:
        Old data from a previous run
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
    """Loads electricity map data with resample to smooth out graph


    Args:
        path: Path of electricity map data
        metric: Smooth on daily/weekly.../ basis. Defaults to "Weeks".

    Returns:
        Dataframe with all electricity map data indexed by dates
    """
    df = pd.read_csv(path)
    df.datetime = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S.%f")
    df.set_index(["datetime"], inplace=True)
    df = df.resample(metric)
    return df


def load_carbon_intensity(path, offset, conf, date="2021-01-01"):
    """Loads carbon intensity for a Region from a certain date for 24 hour interval.
    NOTE California offset = 0.

    Args:
        path: Path of carbon intensity data
        offset: Offset by hour of region
        conf: Runtime configurations to retrieve current timestep
        date: Date to begin loading from. Defaults to "2021-01-01".

    Returns:
        Returns dataframe with carbon intensity data for region, indexed by hours [0,...,24]
    """
    df = pd.read_csv(path)
    start_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    timestamp = int(start_date.timestamp())

    index = df.index[df["timestamp"] == timestamp]
    assert len(index) > 0, f"Date [{start_date}] does not exist in electricity map data"

    start = index[0] + offset
    assert start > 0, start

    end = start + conf.timesteps + 24
    assert end < len(df), "The selected interval overflows the electricity map data"

    # TODO: Consider whether avg or take everything
    df = df["carbon_intensity_avg"].iloc[start:end].reset_index(drop=True)

    return df


def load_request_rate(path, offset, conf, date="2021-01-01"):
    """Loads request rate data for a region and returns its data.
    NOTE California offset = 0.

    Args:
        path: Path of request rate data
        offset: Offset by hour of region
        conf: Runtime configurations to retrieve current timestep
        date: Date to begin loading from. Defaults to "2021-01-01".

    Returns:
        Returns dataframe with request rate data for region, indexed by hours [0,...,24]
    """
    df = pd.read_csv(path)
    start_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc, year=2021)
    timestamp = int(start_date.timestamp())

    index = df.index[df["timestamp"] == timestamp]
    assert len(index) > 0, f"Date [{start_date}] does not exist in request rate data"

    start = index[0] + offset
    assert start > 0, start

    end = start + conf.timesteps + 24
    assert end < len(df), "The selected interval overflows the reqeust rate data"

    df = df["requests"].iloc[start:end].reset_index(drop=True)

    return df

# NOT RELEVANT, BACKUP
# def latencies_per_regions(latency, requests):
#     # [i][:] sum latencies from one region
#     outgoing_requests_per_region = requests.T[:]
#     outgoing_latencies_per_region = latency.T[:]
#     latencies_per_region = [np.dot(l, r)/ len(r) for (l, r) in zip(outgoing_latencies_per_region, outgoing_requests_per_region)]
#     return latencies_per_region


def ui(conf, timestep, request_per_region, servers, servers_per_regions_list):
    """Interactive UI while running for debugging

    Args:
        conf: Runtime configurations to retrieve regions
        timestep: Timesteps
        request_per_region: Dataframe for hourly request rate
        servers: List of servers
        servers_per_regions_list: List of servers per region
    """
    region_names = get_regions(conf)
    print(f"______________________________________ \n TIMESTEP: {timestep}")
    print("Requests per region:")
    [print(f"{region_names[i]} - {request[0]}") for i, request in enumerate(request_per_region)]
    print(" \n SERVERS PER REGION: \n")
    [
        print(f"{region_names[i]} - {servers_per_region}")
        for i, servers_per_region in enumerate(servers_per_regions_list)
    ]
    print("\n Server objects in ServerManager: ")
    print(servers)
    print("______________________________________")


def get_regions(conf):
    """Get regions for continent specified

    Args:
        conf: Runtime configurations to get continent

    Returns:
        Returns array of regions in continent
    """
    if conf.region_kind == "original":
        return REGION_ORIGINAL
    elif conf.region_kind == "europe":
        return REGION_EUROPE
    elif conf.region_kind == "north_america":
        return REGION_NORTH_AMERICA

def servers_distributed(path):
    return pd.read_csv(path)

def load_request_matrix(path = "api/requests/....."):
    ### RETURN NXN MATRIX SPECIFYING WHERE REGIONS GO FROM AND TO
    pd.read_csv(path)
    return requests
