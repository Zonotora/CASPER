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

def required_files(conf):
    region_dir = __region_dir(conf)
    names = [
        "carbon_intensity.csv",
        "latency.csv",
        "request.csv",
        "offset.csv",
    ]
    print("These files must exist:")
    print(region_dir)
    for name in names:
        print(f"\t{name}")

def __region_dir(conf):
    scheduler_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(scheduler_dir, "../data"))
    return os.path.join(data_dir, conf.region_kind)

def load_region_df(conf, file_name):
    try:
        region_dir = __region_dir(conf)
        file_path = os.path.join(region_dir, file_name)
        return pd.read_csv(file_path)
    except:
        print(f"Failed to load file: {file_name}")
        required_files(conf)

def valid_date(conf, file_name):
    df = load_region_df(conf, file_name)
    start_date = datetime.fromisoformat(conf.start_date).replace(tzinfo=timezone.utc)
    timestamp = int(start_date.timestamp())

    index = df.index[df["timestamp"] == timestamp]
    assert len(index) > 0, f"Date [{start_date}] does not exist in file: {file_name}"

    start = index[0]
    assert start > 0, start

    end = start + conf.timesteps + 24
    assert end < len(df), f"The selected interval overflows in file: {file_name}"

    return df, start, end

def load_carbon_intensity(conf):
    df, start, end = valid_date(conf, "carbon_intensity.csv")
    return df.iloc[start:end].reset_index(drop=True)

def load_request(conf):
    df, start, end = valid_date(conf, "request.csv")
    return df.iloc[start:end].reset_index(drop=True)

def load_latency(conf):
    return load_region_df(conf, "latency.csv")

def load_offset(conf):
    return load_region_df(conf, "offset.csv")

def region_names(conf):
    df = load_offset(conf)
    return df.columns