from scheduler.constants import REGION_NAMES
from scheduler.region import Region, load_regions
from scheduler.request import RequestBatch


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
    def __init__(self, conf):
        self.regions = load_regions("electricity_map", conf.start_end_date)
        # TODO: Think about initialization of servers
        self.servers = [Server(10, region) for region in self.regions]

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
        for region, requests in zip(REGION_NAMES, requests_per_region):
            servers = [s for s in self.servers if s.region.name == region]
            request_batches = self.build_request_batches(servers, requests)
            for batch, server in request_batches:
                server.push(batch)

    def build_request_batches(self, servers, requests):
        batches = []
        for server in servers:
            left = server.utilization_left()
            load = min(requests, left)
            # TODO: Add correct name (id)
            batch = RequestBatch("", load, server.region)
            requests -= load
            batches.append((batch, server))
        assert requests == 0, requests

        return batches

    def move(self, servers_per_region):
        """
        We should only move the minimum amount of servers to satisfy the
        number of servers per region

        servers_per_region: specifies the number of servers per region
        """
        count = {region: 0 for region in REGION_NAMES}

        for server in self.servers:
            count[server.region.name] += 1

        # Add servers to each region to satisfy the new server per region constraint
        for region, requested_count in zip(REGION_NAMES, servers_per_region):
            c = count[region]
            while c < requested_count:
                # TODO: Set server capacity in a more generic way
                server = Server(10, region)
                self.servers.append(server)
                c += 1
            count[region] = c
            assert count[region] == requested_count

        # Remove all abundant servers in each region
        for region, requested_count in zip(REGION_NAMES, servers_per_region):
            if count[region] > requested_count:
                indices = [i for i, s in enumerate(self.servers) if s.region == region]
                n = count[region] - requested_count
                assert len(indices) > n
                for i in range(n):
                    index = indices[i]
                    self.servers.pop(index)
