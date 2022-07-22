from tkinter import W
from scheduler.region import Region
from scheduler.request import RequestBatch
import numpy as np


def __get_algorithm(name):
    if name == "latency_greedy":
        return __latency_greedy
    # elif name == "carbon_greedy":
    #     return __carbon_greedy
    # elif name == "carbon_aware":
    #     return __carbon_aware


def __latency_greedy(task_batch, server_manager, t):
    """
    Schedule tasks such that the lowest latency
    servers are filled first.
    """
    regions = server_manager.regions
    utilization_left = server_manager.utilization_left_regions()

    latencies = [task_batch.region.latency(region) for region in regions]
    carbon_intensities = [region.carbon_intensity for region in regions]

    indices = np.argsort(latencies)
    requests_per_region = [0] * len(regions)
    for index in indices:
        name = regions[index].name
        left = utilization_left[name]
        load = min(task_batch.load, left)
        requests_per_region[index] += load
        task_batch.load -= load

    assert task_batch.load == 0, task_batch.load

    # TODO: Make use of dropped requests
    # dropped_requests = task_batch.load

    return latencies, carbon_intensities, requests_per_region


# TODO: Remove or update the following code blocks
# def __carbon_greedy(task_batch, t):
#     """
#     Schedule tasks such that the lowest carbon intensity
#     servers are filled first.
#     """
#     return sorted(
#         [
#             {
#                 "latency": task_batch.region.latency(s.region),
#                 "carbon_intensity": s.carbon_intensity[t],
#                 "server": s,
#             }
#             for s in self.servers
#         ],
#         key=lambda x: x["carbon_intensity"],
#     )


# def __carbon_aware(task_batch, t):
#     """
#     Input: tasks that want to be run.
#     Output: What server each task should be run on
#     satisfying the max latency constraint while having the lowest
#     carbon footprint.

#     List where each entry is (taskbatch, server, latency)

#     Does not split taskbatches, i.e if a server does not
#     have enough capacity, we just move on to the next
#     server.
#     """
#     max_latency = 20
#     data = [
#         {"latency": task_batch.region.latency(s.region), "carbon_intensity": s.carbon_intensity[t], "server": s}
#         for s in self.servers
#     ]
#     below = sorted([x for x in data if x["latency"] <= max_latency], key=lambda x: x["carbon_intensity"])
#     above = sorted([x for x in data if x["latency"] > max_latency], key=lambda x: x["carbon_intensity"])
#     return below + above


def schedule(request_batch, server_manager, algorithm, t):
    alg = __get_algorithm(algorithm)
    return alg(request_batch, server_manager, t)
