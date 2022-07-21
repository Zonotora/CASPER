from scheduler.region import Region
from scheduler.request import RequestBatch
import numpy as np
from collections import deque


class Scheduler:
    def __init__(self, servers, region: Region, scheduler="latency_greedy") -> None:
        self.servers = servers
        self.region = region
        self.alg = self.__get_scheduler(scheduler)
        self.buffer = deque()

    def __get_scheduler(self, name):
        if name == "latency_greedy":
            return self.__latency_greedy
        elif name == "carbon_greedy":
            return self.__carbon_greedy
        elif name == "carbon_aware":
            return self.__carbon_aware

    def __latency_greedy(self, task_batch, dt):
        """
        Schedule tasks such that the lowest latency
        servers are filled first.
        """
        return sorted(
            [
                {
                    "latency": task_batch.region.latency(s.region),
                    "carbon_intensity": s.carbon_intensity[dt],
                    "server": s,
                }
                for s in self.servers
            ],
            key=lambda x: x["latency"],
        )

    def __carbon_greedy(self, task_batch, dt):
        """
        Schedule tasks such that the lowest carbon intensity
        servers are filled first.
        """
        return sorted(
            [
                {
                    "latency": task_batch.region.latency(s.region),
                    "carbon_intensity": s.carbon_intensity[dt],
                    "server": s,
                }
                for s in self.servers
            ],
            key=lambda x: x["carbon_intensity"],
        )

    def __carbon_aware(self, task_batch, dt):
        """
        Input: tasks that want to be run.
        Output: What server each task should be run on
        satisfying the max latency constraint while having the lowest
        carbon footprint.

        List where each entry is (taskbatch, server, latency)

        Does not split taskbatches, i.e if a server does not
        have enough capacity, we just move on to the next
        server.
        """
        max_latency = 20
        data = [
            {"latency": task_batch.region.latency(s.region), "carbon_intensity": s.carbon_intensity[dt], "server": s}
            for s in self.servers
        ]
        below = sorted([x for x in data if x["latency"] <= max_latency], key=lambda x: x["carbon_intensity"])
        above = sorted([x for x in data if x["latency"] > max_latency], key=lambda x: x["carbon_intensity"])
        return below + above

    def schedule(self, plot, task_batch, dt: int):
        self.buffer.append(task_batch)

        i = 0
        while i < len(self.buffer):
            task_batch = self.buffer[i]
            scheduled_task_batch = self.alg(task_batch, dt)

            for scheduled_item in scheduled_task_batch:
                s = scheduled_item["server"]

                if s.update_utilization(task_batch):
                    plot.add(task_batch, scheduled_item, dt)
                    del self.buffer[i]
                    i -= 1
                    break
                else:
                    # send partial batch and update load
                    partial_load = s.get_utilization_left()
                    if partial_load == 0:
                        continue
                    task_batch.reduce_load(partial_load)
                    partial_batch = RequestBatch(task_batch.name + ":partial", partial_load, task_batch.region)
                    s.update_utilization(partial_batch)

                    plot.add(task_batch, scheduled_item, dt)
            i += 1
        data = {}
        for key in ["latency", "carbon_intensity"]:
            data[key] = plot.get(key)

        return data
