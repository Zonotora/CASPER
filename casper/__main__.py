from casper.server import ServerManager
from casper.request import RequestBatch
from casper.parser import parse_arguments
from casper.plot import Plot
from casper.util import save_file, ui
from casper.milp_scheduler import schedule_requests, schedule_servers, compute_args
import sys
import random
import math
import numpy as np


def main():
    """Central function where simulation is run, plots called, requests are injected, etc."""
    random.seed(1234)
    conf = parse_arguments(sys.argv[1:])

    plot = Plot(conf)
    server_manager = ServerManager(conf)

    # How many times we update the servers within one hour
    request_update_interval = 60 // conf.request_update_interval

    for t in range(conf.timesteps + 1):
        # Move all the servers given the next hour's requests rates
        move(conf, server_manager, t)
        # reset server utilization for every server before scheduling requests again
        # we can do this as requests are managed instantaneously for each server
        server_manager.reset()

        for i in range(request_update_interval):
            # get number of requests for timeframe
            batches = build_batches(conf, server_manager, t, request_update_interval=request_update_interval)

            # call the scheduling algorithm
            if conf.replay:
                latency, carbon_intensity, requests_per_region = requests_predetermined(
                    conf, batches, server_manager, t, request_update_interval
                )
            else:
                latency, carbon_intensity, requests_per_region = schedule_requests(
                    conf, batches, server_manager, t, request_update_interval, max_latency=conf.max_latency
                )

            # send requests to servers
            server_manager.send(requests_per_region)

            # save data to plot object
            plot.add(
                server_manager,
                latency,
                carbon_intensity,
                requests_per_region,
                t,
                i,
                request_update_interval,
            )

        # If parser specified to output a runtime UI
        if conf.verbose:
            ui(conf, t, requests_per_region, server_manager.servers, server_manager.servers_per_region())

    if conf.save:
        save_file(conf, plot)

    plot.plot()


def build_batches(conf, server_manager, t, request_update_interval=None):
    """Adds creates batch of work to inject called by main()

    Args:
        conf: Runtime configurations to retrieve work building frequency
        server_manager: Central server manager object that i.e. holds regions
        t: current timestep
        request_update_interval: Frequency at which tasks are built. Defaults to None.

    Returns:
        Batch of requests
    """
    batches = []
    for region in server_manager.regions:
        # Gets per hour
        rate = region.get_requests_per_interval(t)
        if conf.request_rate:
            rate = conf.request_rate
        if request_update_interval:
            rate //= request_update_interval
        batch = RequestBatch(region.name, rate, region)
        batches.append(batch)
    return batches


# Calculate the number of server required to handle the incoming requests to one
# region without the scheduler. Thus the incoming requests are fixed beforehand.
def servers_per_region_predetermined(conf, server_manager, t):
    rates = np.zeros(len(server_manager.regions), dtype=np.float64)
    for region in server_manager.regions:
        rates += region.get_requests_per_interval_per_region(t)

    servers_per_region = np.ceil(rates / conf.server_capacity).astype(np.int64)
    return servers_per_region


def requests_predetermined(conf, request_batches, server_manager, t, request_update_interval):
    carbon_intensity, latency, _, _ = compute_args(conf, request_batches, server_manager, t)

    n = len(server_manager.regions)
    requests_per_region = np.zeros([n, n], dtype=np.float64)
    for i, region in enumerate(server_manager.regions):
        requests_per_region[i] = region.get_requests_per_interval_per_region(t) / request_update_interval

    return latency, carbon_intensity, requests_per_region


def move(conf, server_manager, t):
    """_summary_

    Args:
        conf: _description_
        server_manager: _description_
        t: _description_
    """
    batches = build_batches(conf, server_manager, t)
    if conf.replay:
        servers_per_region = servers_per_region_predetermined(conf, server_manager, t)
    else:
        servers_per_region = schedule_servers(
            conf, batches, server_manager, t, max_latency=conf.max_latency, max_servers=conf.max_servers
        )
        print(servers_per_region)
    # move servers to regions according to scheduling estimation the next hour
    server_manager.move(servers_per_region)


if __name__ == "__main__":
    main()
