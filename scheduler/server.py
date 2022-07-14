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
        self.buffer = []

    def __repr__(self) -> str:
        return f"{self.region:<15} capcity: {self.capacity:<6}"

    def get_utilization_left(self):
        return self.capacity - self.current_utilization

    def update_utilization(self, task_batch):
        if self.current_utilization + task_batch.load <= self.capacity:
            self.current_utilization += task_batch.load
            self.buffer.append(task_batch)
            return True
        return False

    def reset_utilization(self):
        self.current_utilization = 0

    def step(self):
        for task_batch in self.buffer:
            task_batch.lifetime -= 1
            if task_batch.lifetime <= 0:
                self.current_utilization -= task_batch.load
        self.buffer = [task_batch for task_batch in self.buffer if task_batch.lifetime > 0]


def build_servers():
    servers = []
    for name, location in zip(REGION_NAMES, REGION_LOCATIONS):
        df = load(f"electricity_map/{name}.csv", False)
        r = Region(name, location)
        s = Server(1000, r, df)
        servers.append(s)

    return servers
