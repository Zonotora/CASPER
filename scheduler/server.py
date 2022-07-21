from scheduler.constants import REGION_NAMES
from scheduler.region import Region
from scheduler.request import RequestBatch
from scheduler.util import load_region_data


class Server:
    """
    An artificial server with a carbon trace,
    latency and capacity.
    """

    def __init__(self, capacity: int, region: Region):
        self.capacity = capacity
        self.utilization = 0
        self.region = region

    def __repr__(self) -> str:
        return f"{self.region:<15} capcity: {self.capacity:<6}"

    def utilization_left(self):
        return self.capacity - self.utilization

    def push(self, request_batch):
        """
        Push batch of requests to buffer. Batches of requests are removed
        from the buffer when they have been completed.
        """
        assert self.utilization + request_batch.load <= self.capacity, self.utilization + request_batch.load

        self.utilization += request_batch.load

    def reset_utilization(self):
        self.utilization = 0


class ServerManager:
    def __init__(self):
        self.servers = []
        self.region_data = load_region_data("electricity_map")

    def send(self, requests_per_region):
        """
        Distributes requests to each server for each region
        """
        for i in range(requests_per_region):
            requests = requests_per_region[i]
            servers = [s for s in self.servers if s.region == REGION_NAMES[i]]
            request_batches = self.build_request_batches(servers, requests)
            for batch, server in request_batches:
                server.push(batch)

    def build_request_batches(self, servers, requests):
        batches = []
        for server in servers:
            left = server.utilization_left()
            load = min(requests, left)
            # TODO: Add correct name (id)
            batch = RequestBatch("", load, 0, server.region)
            requests -= load
            batches.append((batch, server))
        assert requests == 0

        return batches

    def move(self, servers_per_region):
        """
        We should only move the minimum amount of servers to satisfy the
        number of servers per region

        servers_per_region: specifies the number of servers per region
        """
        raise NotImplementedError
        count = {name: 0 for name in REGION_NAMES}

        for s in self.servers:
            count[s.region.name] += 1

        buffer = [0] * len(servers_per_region)
        for name, c in zip(REGION_NAMES, servers_per_region):
            if c < count[name]:
                pass
