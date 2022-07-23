import os
from scheduler.util import load_carbon_intensity, load_request_rate
from scheduler.constants import REGION_NAMES, REGION_LOCATIONS, REGION_OFFSETS


class Region:
    def __init__(self, name, location, carbon_intensity, requests_per_hour, offset) -> None:
        self.name = name
        self.location = location
        self.requests_per_hour = requests_per_hour
        self.carbon_intensity = carbon_intensity
        self.offset = offset

    def get_requests_per_hour(self, t):
        return self.requests_per_hour.iloc[t + self.offset]

    def latency(self, other):
        (x1, y1) = self.location
        (x2, y2) = other.location
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def __repr__(self) -> str:
        return self.name

    def __format__(self, __format_spec: str) -> str:
        return format(self.name, __format_spec)


def load_regions(date):
    regions = []
    d = "api"
    for name in REGION_NAMES:
        file = f"{name}.csv"
        path = os.path.join(d, file)
        location = REGION_LOCATIONS[name]
        offset = REGION_OFFSETS[name]

        request_path = os.path.join(d, "requests.csv")
        requests_per_hour = load_request_rate(request_path, offset, date)
        carbon_intensity = load_carbon_intensity(path, offset, date)
        region = Region(name, location, carbon_intensity, requests_per_hour, offset)
        regions.append(region)
    return regions
