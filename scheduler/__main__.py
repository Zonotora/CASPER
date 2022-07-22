from turtle import update
from scheduler.server import ServerManager
from scheduler.request import RequestBatch
from scheduler.parser import parse_arguments
from scheduler.plot import Plot
from scheduler.util import save_file, load_file
from scheduler.milp_sched import schedule
import sys
import random


def main():
    """
    Init the servers. Generate some fake workload.
    Schedule and run the workload. Get the latency
    and carbon footprint summary. Report it.
    """
    random.seed(1234)
    conf = parse_arguments(sys.argv[1:])
    if conf.file_to_load:
        data = load_file(conf.file_to_load)
        plot = Plot(conf, data=data)
        plot.plot()
        exit()

    plot = Plot(conf)
    server_manager = ServerManager()

    request_update_interval = 60 // conf.request_update_interval

    for t in range(conf.timesteps):
        for _ in range(request_update_interval):
            # reset server utilization for every server before scheduling requests again
            # we can do this as requests are managed instantaneously for each server
            server_manager.reset()
            # get number of requests for timeframe
            # TODO: Change this to dynamic requests
            request_batch = RequestBatch("", 36, server_manager.regions[0])
            # call the scheduling algorithm
            latency, carbon_intensity, requests_per_region = schedule(request_batch, server_manager, conf.algorithm, t)
            # send requests to servers
            server_manager.send(requests_per_region)
            # update plots
            update_plot(plot, t, latency, carbon_intensity, requests_per_region)

        # move servers to regions according to scheduling estimation the next hour
        server_manager.move([1, 1, 1, 1])

    if conf.file_to_save:
        save_file(conf.file_to_save, plot.data)

    plot.plot()


def update_plot(plot, t, latency, carbon_intensity, requests_per_region):
    for i in range(len(requests_per_region)):
        load = requests_per_region[i]
        if load == 0:
            continue

        data = {"latency": latency[i], "carbon_emissions": carbon_intensity[i] * load}
        plot.add(data, t)


if __name__ == "__main__":
    main()
