from typing import List
import numpy as np


class Scheduler:
    def __init__(self, servers, scheduler="latency_greedy") -> None:
        self.servers = servers
        self.alg = self.__get_scheduler(scheduler)

    def __get_scheduler(self, name):
        if name == "latency_greedy":
            return self.__latency_greedy
        elif name == "carbon_greedy":
            return self.__carbon_greedy
        elif name == "carbon_aware":
            return self.__carbon_aware

    def __latency_greedy(self, tasks, dt):
        """
        Schedule tasks such that the lowest latency
        servers are filled first.
        """
        scheduled_tasks = {}
        for t in tasks:
            data = [
                {"latency": t.region.latency(s.region), "carbon_intensity": s.carbon_intensity[dt], "server": s}
                for s in self.servers
            ]
            scheduled_tasks[t] = sorted(data, key=lambda x: x["latency"])
        return scheduled_tasks

    def __carbon_greedy(self, tasks, dt):
        """
        Schedule tasks such that the lowest carbon intensity
        servers are filled first.
        """
        scheduled_tasks = {}
        for t in tasks:
            data = [
                {"latency": t.region.latency(s.region), "carbon_intensity": s.carbon_intensity[dt], "server": s}
                for s in self.servers
            ]
            scheduled_tasks[t] = sorted(data, key=lambda x: x["carbon_intensity"])
        return scheduled_tasks

    def __carbon_aware(self, tasks, dt):
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
        scheduled_tasks = {}
        max_latency = 20
        for t in tasks:
            data = [
                {"latency": t.region.latency(s.region), "carbon_intensity": s.carbon_intensity[dt], "server": s}
                for s in self.servers
            ]
            below = sorted([x for x in data if x["latency"] <= max_latency], key=lambda x: x["carbon_intensity"])
            above = sorted([x for x in data if x["latency"] > max_latency], key=lambda x: x["carbon_intensity"])
            scheduled_tasks[t] = below + above
        return scheduled_tasks

    def schedule(self, tasks, dt):
        scheduled_tasks = self.alg(tasks, dt)
        data = {"latency": [], "carbon_intensity": []}

        for task in scheduled_tasks:
            for scheduled_item in scheduled_tasks[task]:

                s = scheduled_item["server"]
                latency = scheduled_item["latency"]
                carbon_intensity = scheduled_item["carbon_intensity"]

                if s.update_utilization(task.load):
                    data["latency"].append(latency * task.load)
                    data["carbon_intensity"].append(carbon_intensity * task.load)
                    task.reduce_load(task.load)
                    break
                else:
                    # send partial batch and update load
                    partial_load = s.get_utilization_left()
                    if partial_load == 0:
                        continue
                    task.reduce_load(partial_load)
                    s.update_utilization(partial_load)

                    data["latency"].append(latency * task.load)
                    data["carbon_intensity"].append(carbon_intensity * task.load)

        data["latency"] = np.mean(data["latency"])
        data["carbon_intensity"] = np.mean(data["carbon_intensity"])
        return data
