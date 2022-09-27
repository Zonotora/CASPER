from scheduler.server import ServerManager
from scheduler.request import RequestBatch
from scheduler.parser import parse_arguments
from scheduler.plot import Plot
from scheduler.util import save_file, ui
from scheduler.milp_scheduler import schedule_requests, schedule_servers
import sys
import random


def main():
    """Central function where simulation is run, plots called, requests are injected, etc.
    """
    random.seed(1234)
    conf = parse_arguments(sys.argv[1:])

    # if conf.load:
    #     data = load_file(conf.load)
    #     plot = Plot(conf, data=data)
    #     plot.plot()
    #     exit()

    plot = Plot(conf)
    server_manager = ServerManager(conf)

    #Frequency of which to create more requests
    request_update_interval = 60 // conf.request_update_interval

    for t in range(conf.timesteps + 1):
        # Move all the servers given the next hour's requests rates
        move(conf, server_manager, t)

        for i in range(request_update_interval):
            # get number of requests for timeframe
            batches = build_batches(conf, server_manager, t, request_update_interval=request_update_interval)

            # call the scheduling algorithm
            latency, carbon_intensity, requests_per_region = schedule_requests(
                conf, batches, server_manager, t, request_update_interval, max_latency=conf.latency
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
        #Gets per hour
        rate = region.get_requests_per_interval(t)
        if conf.rate:
            rate = conf.rate
        if request_update_interval:
            rate //= request_update_interval
        batch = RequestBatch(region.name, rate, region)
        batches.append(batch)
    return batches


def move(conf, server_manager, t):
    """_summary_

    Args:
        conf: _description_
        server_manager: _description_
        t: _description_
    """
    batches = build_batches(conf, server_manager, t)
    servers_per_region = schedule_servers(
        conf, batches, server_manager, t, max_latency=conf.latency, max_servers=conf.max_servers
    )
    # move servers to regions according to scheduling estimation the next hour
    server_manager.move(servers_per_region)


if __name__ == "__main__":
    main()
