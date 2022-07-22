import os
from scheduler.util import load_electricity_data, load_request_rate
from scheduler.constants import REGION_NAMES, REGION_LOCATIONS, REGION_OFFSETS


class Region:
    def __init__(self, name, location, requests_per_hour, carbon_intensity) -> None:
        self.name = name
        self.location = location
        self.requests_per_hour = requests_per_hour
        self.carbon_intensity = carbon_intensity
        self.offset = REGION_OFFSETS[self.name]

    def get_request_by_hour(self, i):
        return self.requests_per_hour.iloc[i]

    def latency(self, other):
        (x1, y1) = self.location
        (x2, y2) = other.location
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def __repr__(self) -> str:
        return self.name

    def __format__(self, __format_spec: str) -> str:
        return format(self.name, __format_spec)



def load_regions(self, d, date, resample=False, resample_metric="W"):
    regions = []
    requests = load_request_rate(date=date)
    for name in REGION_NAMES:
        file = f"{name}.csv"
        path = os.path.join(d, file)
        location = REGION_LOCATIONS[name]
        carbon_intensity = load_electricity_data(path, date, self.offset,
            resample=resample, resample_metric=resample_metric)
        #carbon_intensity = df["carbon_intensity_avg"]
        requests_per_hour = requests[name]
        region = Region(name, location, requests_per_hour, carbon_intensity)
        regions.append(region)
    return regions
