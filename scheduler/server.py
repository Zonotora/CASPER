from scheduler.constants import REGION_NAMES, REGION_LOCATIONS
from scheduler.region import Region
from scheduler.util import load


class Server:
    """
    An artificial server with a carbon trace,
    latency and capacity.
    """

    def __init__(self, capacity: int, region: Region, carbon_data):
        self.capacity = capacity
        self.current_utilization = 0
        self.region = region
        self.carbon_data = carbon_data
        self.carbon_intensity = carbon_data["carbon_intensity_avg"]

    def __repr__(self) -> str:
        return f"{self.region:<15} capcity: {self.capacity:<6}"

    def get_utilization_left(self):
        return self.capacity - self.current_utilization

    def update_utilization(self, task_batch):
        if self.current_utilization + task_batch.load <= self.capacity:
            self.current_utilization += task_batch.load
            return True
        return False

    def reset_utilization(self):
        self.current_utilization = 0


def build_servers():
    servers = []
    i = 1
    for name, location in zip(REGION_NAMES, REGION_LOCATIONS):
        df = load(f"electricity_map/{name}.csv", False)
        r = Region(name, location)
        s = Server(10 * i, r, df)
        servers.append(s)
        i += 1

    return servers
