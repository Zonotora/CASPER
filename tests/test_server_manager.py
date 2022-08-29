import pytest
from scheduler.server import ServerManager
from scheduler.region import Region
from scheduler.parser import parse_arguments

import pandas as pd

from scheduler.util import get_regions


def test_manager():
    conf = parse_arguments([])
    region_names = get_regions(conf)
    rqs = pd.DataFrame(data=[1])
    # Create regions
    regions = [
        Region(name=region, location=0, carbon_intensity=10, requests_per_hour=rqs, offset=0) for region in region_names
    ]
    server_manager = ServerManager(conf, regions=[])

    # Assert regions are not initiated
    assert len(server_manager.regions) == 0

    server_manager = ServerManager(conf, regions=regions)

    # Assert n.o. regions correct when initiated
    assert len(server_manager.regions) == len(region_names)

    servers_per_region = server_manager.servers_per_region()
    correct_servers_per_region = [0, 0, 0, 0]

    # Assert servers are not placed in the beginning
    assert servers_per_region == correct_servers_per_region

    server_manager.move([1, 1, 1, 1])

    # Assert servers are placed correctly
    assert server_manager.servers_per_region() == [1, 1, 1, 1]

    # Assert they are unutilized
    assert server_manager.utilization_left_regions() == [conf.server_capacity for _ in range(4)]

    dropped_requests_per_region = []
    for i in range(len(region_names)):
        region = region_names[i]
        requests = int(rqs[0])
        print(requests)
        # All servers in the {region} we should send our request batches
        servers = [s for s in server_manager.servers if s.region.name == region]
        # Craete request batches that are destined to {region}
        server_loads = server_manager.build_server_loads(servers, requests)
        for server, load in server_loads:
            server.push(load)

    # Assert each server has a load of an task = 1
    assert server_manager.utilization_left_regions() == [conf.server_capacity - 1 for _ in range(4)]
