from fnmatch import translate
import os
import pandas as pd
from scheduler.util import load_carbon_intensity, load_request_rate
from scheduler.constants import REGION_LOCATIONS, REGION_OFFSETS
from scheduler.util import get_regions



class Region:
    """
    Region object to hold and get region-specific data.
    """
    def __init__(self, name, location, carbon_intensity, requests_per_hour) -> None:
        """Input properties when region is instantiated

        Args:
            name: Name of region
            location: Deprecated for estimating latency
            carbon_intensity: Average carbon intensity during specified timeframe
            requests_per_hour: Requests per hour during specified timeframe
            latency_df : Replaces latency estimation with real latency data
        """
        self.name = name
        self.location = location
        self.requests_per_hour = requests_per_hour
        self.carbon_intensity = carbon_intensity
        self.latency_df = pd.read_csv("api/cloudping/latency_50th.csv")

    def get_requests_per_hour(self, t):
        """Get requests per hour for a timestep

        Args:
            t: timestep

        Returns:
            Integer of requests for that hour
        """
        return self.requests_per_hour.iloc[t]

    # def latency(self, other):
    #     (x1, y1) = self.location
    #     (x2, y2) = other.location
    #     return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def latency(self, other):
        """Gives latency from one region to another using cloudping data specified in README

        Args:
            self: Region sending a request
            other: Region recieving request

        Returns:
            Returns round-trip latency from region "self" to region "other"
        """
        df = self.latency_df
        i = df.columns.get_loc(self.name)
        j = df.columns.get_loc(other.name)
        return df.iloc[i, j]

    def __repr__(self) -> str:
        return self.name

    def __format__(self, __format_spec: str) -> str:
        return format(self.name, __format_spec)


def load_regions(conf):
    """Loads data for all regions from csv files and returns all regions

    Args:
        conf: Decides which continent of regions to load

    Returns:
        List of all region objects containing their specific data
    """
    date = conf.start_date
    regions = []
    d = "api"
    kind = ""
    if conf.region_kind == "original":
        kind = "original"
    elif conf.region_kind == "europe":
        kind = "europe"
    elif conf.region_kind == "north_america":
        kind = "north_america"
    d = os.path.join(d, kind)

    for name in get_regions(conf):
        file = f"{name}.csv"
        path = os.path.join(d, file)
        location = REGION_LOCATIONS[name]
        # hardcoded offsets
        offset = REGION_OFFSETS[name]

        request_path = "api/requests.csv"
        requests_per_hour = load_request_rate(request_path, offset, conf, date)
        carbon_intensity = load_carbon_intensity(path, offset, conf, date)
        region = Region(name, location, carbon_intensity, requests_per_hour)
        regions.append(region)
    return regions
