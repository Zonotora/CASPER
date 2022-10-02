from casper.server import ServerManager
from casper.request import RequestBatch
from casper.parser import parse_arguments
from casper.plot import Plot
from casper.util import save_file, ui
from casper.milp_scheduler import schedule_requests, schedule_servers, compute_args
import sys
import random
import math


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

        for i in range(request_update_interval):
            # get number of requests for timeframe
            batches = build_batches(conf, server_manager, t, request_update_interval=request_update_interval)

            # call the scheduling algorithm
            if conf.replay:
                latency, carbon_intensity, requests_per_region = requests_with_incoming(
                    conf, batches, server_manager, t
                )
            else:
                latency, carbon_intensity, requests_per_region = schedule_requests(
                    conf, batches, server_manager, t, request_update_interval, max_latency=conf.max_latency
                )

            # send requests to servers
            server_manager.send(requests_per_region)

            # dropped requests
            dropped_requests_per_region = [0] * len(batches)
            if len(server_manager.servers) == 0:
                for i in range(len(batches)):
                    dropped_requests_per_region[i] = batches[i].load

            # save data to plot object
            plot.add(
                server_manager,
                latency,
                carbon_intensity,
                requests_per_region,
                dropped_requests_per_region,
                t,
                i,
                request_update_interval,
            )

            # reset server utilization for every server before scheduling requests again
            # we can do this as requests are managed instantaneously for each server
            server_manager.reset()

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
def servers_per_region_with_incoming(conf, server_manager, t):
    servers_per_region = [0] * len(server_manager.regions)
    for i, region in enumerate(server_manager.regions):
        rate = region.get_incoming_per_interval(t)
        n_servers = math.ceil(rate / conf.server_capacity)
        servers_per_region[i] = n_servers
    return servers_per_region


def requests_with_incoming(conf, request_batches, server_manager, t):
    carbon_intensity, latency, _, _ = compute_args(conf, request_batches, server_manager, t)
    requests_per_region = np.array([region.get_incoming_per_interval(t) for region in server_manager.regions])

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
        servers_per_region = servers_per_region_with_incoming(conf, server_manager, t)
    else:
        servers_per_region = schedule_servers(
            conf, batches, server_manager, t, max_latency=conf.max_latency, max_servers=conf.max_servers
        )
    # move servers to regions according to scheduling estimation the next hour
    server_manager.move(servers_per_region)


if __name__ == "__main__":
    main()
