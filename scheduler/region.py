from scheduler.constants import REGION_OFFSETS


class Region:
    def __init__(self, name, location, requests_per_hour) -> None:
        self.name = name
        self.location = location
        self.requests_per_hour = requests_per_hour
        self.offset = REGION_OFFSETS[self.name]


    def get_request_by_hour(self, i):
        return self.requests.per_hour.iloc(i)

    def latency(self, other):
        (x1, y1) = self.location
        (x2, y2) = other.location
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def __repr__(self) -> str:
        return self.name

    def __format__(self, __format_spec: str) -> str:
        return format(self.name, __format_spec)
