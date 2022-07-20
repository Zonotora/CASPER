from scheduler.server import build_servers
from scheduler.request import RequestBatch
from scheduler.constants import REGION_LOCATIONS, REGION_NAMES
from scheduler.parser import parse_arguments
from scheduler.region import Region
from scheduler.plot import Plot
from scheduler.lp_sched import schedule
from scheduler.util import save_file, load_file
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

    servers = build_servers()
    regions = [Region(name, location) for name, location in zip(REGION_NAMES, REGION_LOCATIONS)]
    plot = Plot(conf)
    id = 0

    for t in range(conf.timesteps):
        for _ in range(0, conf.tasks_per_timestep):
            # get list of servers for each task batch where the
            # scheduler thinks it is best to place each batch
            for i in range(len(regions)):
                task_batch = RequestBatch(f"Task {id}", 3, 5, regions[i])
                latency, carbon_intensity, requests = schedule(task_batch, servers, conf.algorithm, t)
                update_servers(plot, servers, task_batch, t, latency, carbon_intensity, requests)
                id += 1

            for s in servers:
                s.step()

    if conf.file_to_save:
        save_file(conf.file_to_save, plot.data)

    plot.plot()


def update_servers(plot, servers, task_batch, t, latency, carbon_intensity, requests):

    for i in range(len(requests)):
        load = requests[i]
        if load == 0:
            continue
        batch = RequestBatch(f"{task_batch.name}_{i}", requests[i], task_batch.lifetime, task_batch.region)
        servers[i].update_utilization(batch)

        data = {"latency": latency[i], "carbon_emissions": carbon_intensity[i] * load, "server": servers[i]}
        plot.add(batch, data, t)


if __name__ == "__main__":
    main()
