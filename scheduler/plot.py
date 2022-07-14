import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scheduler.constants import REGION_NAMES, TASK_PER_TIMESTEP


class Plot:
    def __init__(self, conf) -> None:
        self.conf = conf
        self.data = [[] for _ in range(conf.timesteps * conf.tasks_per_hour)]

    def add(self, task_batch, scheduled_item, dt, ds):
        data = {}
        for key in ["latency", "carbon_intensity"]:
            data[key] = scheduled_item[key] * task_batch.load

        s = scheduled_item["server"]
        data["server"] = {
            "name": s.region.name,
            "utilization": s.current_utilization,
            "buffer_size": len(s.buffer),
        }

        self.data[dt * TASK_PER_TIMESTEP + ds].append(data)

    def get(self, key):
        return np.array([np.mean(list(map(lambda y: y[key], x))) for x in self.data])

    def __preprocess(self, key: str, all=True, should_index_server=False, kind="mean"):
        def numpy_alg(x):
            if len(x) == 0:
                return 0
            if kind == "mean":
                return np.mean(x)
            elif kind == "min":
                return np.min(x)
            elif kind == "max":
                return np.max(x)

        def index_server(y, key, should_index_server=False):
            if should_index_server:
                return y["server"][key]
            return y[key]

        if all:
            mean = np.array(
                [numpy_alg(list(map(lambda y: index_server(y, key, should_index_server), x))) for x in self.data]
            )
            std = np.array(
                [np.std(list(map(lambda y: index_server(y, key, should_index_server), x))) for x in self.data]
            )
        else:
            values_with_names = [
                list(map(lambda y: (index_server(y, key, should_index_server), y["server"]["name"]), x))
                for x in self.data
            ]
            mean = np.zeros(shape=(len(values_with_names), len(REGION_NAMES)))
            std = np.zeros(shape=(len(values_with_names), len(REGION_NAMES)))
            for i, item in enumerate(values_with_names):
                values = {name: [] for name in REGION_NAMES}
                for (v, name) in item:
                    values[name].append(v)
                for name in REGION_NAMES:
                    values[name] = (numpy_alg(values[name]), np.std(values[name]))

                for j in range(len(REGION_NAMES)):
                    name = REGION_NAMES[j]
                    mean[i, j] = values[name][0]
                    std[i, j] = values[name][1]
            mean = pd.DataFrame(data=mean, columns=REGION_NAMES).fillna(0)
            std = pd.DataFrame(data=std, columns=REGION_NAMES).fillna(0)

        return mean, std

    def plot(self):
        mean_latency, std_latency = self.__preprocess("latency")
        mean_carbon_intensity, std_carbon_intensity = self.__preprocess("carbon_intensity")
        mean_utilization, std_utilization = self.__preprocess("utilization", should_index_server=True, kind="max")
        graphs = {
            "latency": [mean_latency, std_latency],
            "carbon_intensity": [mean_carbon_intensity, std_carbon_intensity],
            "utilization": [mean_utilization, std_utilization],
        }

        fig = plt.figure(figsize=(18, 14))
        x = range(self.conf.timesteps * self.conf.tasks_per_hour)
        i = 0

        for key in graphs:
            [mean, std] = graphs[key]
            error = 1.96 * std / np.sqrt(len(x))

            ax = plt.subplot(2, 3, i + 1)
            ax.set_title(key)
            ax.plot(x, mean, label=key)
            ax.fill_between(x, mean - error, mean + error, alpha=0.3)
            # ax.legend()
            i += 1

        mean_servers_latency, std_servers_latency = self.__preprocess("latency", False)
        mean_servers_carbon_intensity, std_servers_carbon_intensity = self.__preprocess("carbon_intensity", False)
        mean_servers_utilization, std_servers_utilization = self.__preprocess(
            "utilization", all=False, should_index_server=True, kind="max"
        )
        graphs_servers = {
            "latency": [mean_servers_latency, std_servers_latency],
            "carbon_intensity": [mean_servers_carbon_intensity, std_servers_carbon_intensity],
            "utilization": [mean_servers_utilization, std_servers_utilization],
        }
        for key in graphs_servers:
            [mean, std] = graphs_servers[key]
            error = 1.96 * std / np.sqrt(len(x))

            ax = plt.subplot(2, 3, i + 1)
            ax.set_title(key)
            mean.plot(kind="line", ax=ax)
            i += 1

        plt.show()
