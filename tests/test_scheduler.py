import pytest

from scheduler.request import RequestBatch
from scheduler.region import Region
from scheduler.constants import REGION_NAMES, REGION_LOCATIONS
from scheduler.parser import parse_arguments
from scheduler.lp_sched import schedule

import numpy as np


def test_carbon_greedy_with_one_scheduler_0_24(df_carbon_intensity, servers_infty):
    conf = parse_arguments(["-a", "carbon_greedy"])
    region = Region(REGION_NAMES[0], REGION_LOCATIONS[0])

    for t in range(conf.timesteps):
        task_batch = RequestBatch("Task 1", 1, region)
        _, carbon_intensity, requests = schedule(task_batch, servers_infty, conf.algorithm, t)
        indices = np.nonzero(requests)
        value = np.array(carbon_intensity)[indices]
        assert value == df_carbon_intensity[0:24].iloc[t].min()


def test_latency_greedy_with_one_scheduler_0_24(servers_infty):
    conf = parse_arguments(["-a", "latency_greedy"])
    region = Region(REGION_NAMES[0], REGION_LOCATIONS[0])

    for t in range(conf.timesteps):
        task_batch = RequestBatch("Task 1", 1, region)
        latency, _, requests = schedule(task_batch, servers_infty, conf.algorithm, t)
        indices = np.nonzero(requests)
        value = np.array(latency)[indices]
        assert value == 0
