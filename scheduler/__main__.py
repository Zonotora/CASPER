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

    server_manager = ServerManager()
    plot = Plot(conf)

    request_update_interval = 60 // conf.request_update_interval

    for t in range(conf.timesteps):
        # reset server utilization for every server before scheduling requests again
        # we can do this as requests are managed instantaneous for each server
        server_manager.reset()

        for _ in range(request_update_interval):
            # get number of requests for timeframe
            requests = 1000
            # call the scheduling algorithm
            latency, carbon_intensity, requests = schedule(requests, conf.algorithm, t)
            # send requests to servers
            server_manager.send()

        # move servers to regions according to scheduling estimation the next hour
        server_manager.move()

    if conf.file_to_save:
        save_file(conf.file_to_save, plot.data)

    plot.plot()


def update_servers(plot, servers, task_batch, t, latency, carbon_intensity, requests):

    for i in range(len(requests)):
        load = requests[i]
        if load == 0:
            continue
        batch = RequestBatch(f"{task_batch.name}_{i}", requests[i], task_batch.region)
        servers[i].update_utilization(batch)

        data = {"latency": latency[i], "carbon_emissions": carbon_intensity[i] * load, "server": servers[i]}
        plot.add(batch, data, t)


if __name__ == "__main__":
    main()
