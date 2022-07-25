from scheduler.constants import REGION_NAMES, SERVER_CAPACITY
from scheduler.region import Region, load_regions
from scheduler.request import RequestBatch
import logging


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
        return f"Server({self.region})"

    def utilization_left(self):
        return self.capacity - self.utilization

    def push(self, load):
        """
        Push batch of requests to buffer. Batches of requests are removed
        from the buffer when they have been completed.
        """
        assert self.utilization + load <= self.capacity, (
            self.utilization + load,
            self.capacity,
        )

        self.utilization += load

    def reset_utilization(self):
        self.utilization = 0


class ServerManager:
    def __init__(self, conf):
        self.regions = load_regions(conf.start_date)
        # TODO: Think about initialization of servers
        self.servers = [Server(SERVER_CAPACITY, region) for region in self.regions]

    def reset(self):
        """
        Reset utilization for every server
        """
        for server in self.servers:
            server.reset_utilization()

    def utilization_left_regions(self):
        utilization_left = {region: 0 for region in REGION_NAMES}

        for server in self.servers:
            utilization_left[server.region.name] += server.utilization_left()

        return [utilization_left[region] for region in REGION_NAMES]

    def servers_per_region(self):
        count = {region: 0 for region in REGION_NAMES}

        for server in self.servers:
            count[server.region.name] += 1

        return [count[region] for region in REGION_NAMES]

    def send(self, requests_per_region):
        """
        Distributes requests to each server for each region

        requests_per_region: the number of requests that should be
        distributed across servers in a region
        """
        dropped_requests_per_region = []
        for i in range(len(REGION_NAMES)):
            region = REGION_NAMES[i]
            # All requests to a {region}
            requests = sum(requests_per_region[:, i])
            # All servers in the {region} we should send our request batches
            servers = [s for s in self.servers if s.region.name == region]
            # Craete request batches that are destined to {region}
            server_loads, dropped_requests = self.build_server_loads(servers, requests)
            dropped_requests_per_region.append(dropped_requests)

            for server, load in server_loads:
                server.push(load)

        return dropped_requests_per_region

    def build_server_loads(self, servers, requests):
        initial_requests = requests
        loads = []
        for server in servers:
            left = server.utilization_left()
            load = min(left, requests)
            requests -= load
            assert requests >= 0, requests
            loads.append((server, load))

        if requests > 0:
            logging.warning(
                f"Dropping requests: {requests}, initially: {initial_requests}, server_length: {len(servers)}"
            )

        return loads, requests

    def move(self, servers_per_region):
        """
        We should only move the minimum amount of servers to satisfy the
        number of servers per region

        servers_per_region: specifies the number of servers per region
        """
        count = {region: 0 for region in REGION_NAMES}

        for server in self.servers:
            count[server.region.name] += 1

        # self.servers = []
        # for region, requested_count in zip(self.regions, servers_per_region):
        #     for _ in range(requested_count):
        #         server = Server(SERVER_CAPACITY, region)
        #         self.servers.append(server)

        # Remove all abundant servers in each region
        for region_name, requested_count in zip(REGION_NAMES, servers_per_region):
            if count[region_name] > requested_count:
                indices = [i for i, s in enumerate(self.servers) if s.region.name == region_name]
                n = count[region_name] - requested_count
                assert n >= 0, n
                assert n <= len(indices), (n, len(indices))
                for i in range(n - 1, -1, -1):
                    index = indices[i]
                    self.servers.pop(index)

        # Add servers to each region to satisfy the new server per region constraint
        for region, requested_count in zip(self.regions, servers_per_region):
            c = count[region.name]
            while c < requested_count:
                # TODO: Set server capacity in a more generic way
                server = Server(SERVER_CAPACITY, region)
                self.servers.append(server)
                c += 1
            count[region.name] = c

        for region, requested_count in zip(self.regions, servers_per_region):
            s = sum([1 for s in self.servers if s.region.name == region.name])
            assert s == requested_count, (s, requested_count, region)
