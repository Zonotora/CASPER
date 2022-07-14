from scheduler.server import build_servers
from scheduler.task import TaskBatch
from scheduler.scheduler import Scheduler
from scheduler.constants import TIMESTEPS, TASK_PER_TIMESTEP, REGION_LOCATIONS, REGION_NAMES
from scheduler.parser import parse_arguments
from scheduler.region import Region
from scheduler.plot import Plot
import sys
import random
import numpy as np


def main():
    """
    Init the servers. Generate some fake workload.
    Schedule and run the workload. Get the latency
    and carbon footprint summary. Report it.
    """
    random.seed(1234)
    conf = parse_arguments(sys.argv[1:])

    servers = build_servers()
    schedulers = [
        Scheduler(servers, Region(name, location), scheduler=conf.algorithm)
        for name, location in zip(REGION_NAMES, REGION_LOCATIONS)
    ]
    plot = Plot(TIMESTEPS)
    id = 0

    for dt in range(TIMESTEPS):
        for _ in range(0, TASK_PER_TIMESTEP):
            # get list of servers for each task batch where the
            # scheduler thinks it is best to place each batch
            indices = np.random.choice(len(schedulers), len(schedulers), replace=False)
            for i in indices:
                scheduler = schedulers[i]
                task_batch = TaskBatch(f"Task {id}", 1, 1, scheduler.region)
                data = scheduler.schedule(plot, task_batch, dt)
                id += 1

            for s in servers:
                s.step()

    plot.plot(conf)


if __name__ == "__main__":
    main()
