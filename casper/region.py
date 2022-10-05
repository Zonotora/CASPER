import os
import pandas as pd
import numpy as np
import math
from casper.util import load_carbon_intensity, load_request, load_latency, load_offset, region_names


class Region:
    """
    Region object to hold and get region-specific data.
    """

    def __init__(self, conf, name, carbon_intensity, request, latency, offset) -> None:
        self.name = name
        self.request = request
        self.carbon_intensity = carbon_intensity
        self._latency = latency
        self.offset = offset
        self.region_names = region_names(conf)

    def __repr__(self):
        return f"Region({self.name})"

    def __format__(self, __format_spec: str) -> str:
        return format(self.name, __format_spec)

    def get_requests_per_interval(self, t):
        return self.request.iloc[t][self.region_names].sum()

    def get_requests_per_interval_per_region(self, t):
        return self.request.iloc[t][self.region_names].to_numpy(dtype=np.float64)

    def latency(self, region):
        assert isinstance(region, Region)
        return self._latency[region.name].values[0]

    def haversine_latency(self, other):
        """
            Uses the haversine distance d [km] between two points
            and calculates latency as L=0.022*0.62*d+m [ms].

            TODO: Add random fluctuations sd=2.5 ms ?
        Args:
            other: The other region we want to calculate distance to
        """
        assert isinstance(other, Region)

        lat1 = self.location[0] * math.pi / 180
        lat2 = other.location[0] * math.pi / 180
        dlat = lat2 - lat1
        dlon = (other.location[1] - self.location[1]) * math.pi / 180

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = 6371 * c

        return 0.022 * 0.62 * d + 4.862


def load_regions(conf):
    """Loads data for all regions from csv files and returns all regions

    Args:
        conf: Decides which continent of regions to load

    Returns:
        List of all region objects containing their specific data
    """
    regions = []

    carbon_intensity_df = load_carbon_intensity(conf)
    latency_df = load_latency(conf)
    offset_df = load_offset(conf)

    for name in region_names(conf):
        latency = latency_df.loc[latency_df.iloc[:, 0] == name]
        request = load_request(conf, name)
        carbon_intensity = carbon_intensity_df[name]
        offset = offset_df[name].values[0]

        region = Region(conf, name, carbon_intensity, request, latency, offset)
        regions.append(region)
    return regions
