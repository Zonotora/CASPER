import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scheduler.constants import REGION_NAMES


class Plot:
    def __init__(self, timesteps) -> None:
        self.timesteps = timesteps
        self.data = [[] for _ in range(timesteps)]

    def add(self, task_batch, scheduled_item, dt):
        data = {}
        for key in ["latency", "carbon_intensity"]:
            data[key] = scheduled_item[key] * task_batch.load

        s = scheduled_item["server"]
        data["server"] = {
            "name": s.region.name,
            "utilization": s.current_utilization,
            "buffer_size": len(s.buffer),
        }

        self.data[dt].append(data)

    def __preprocess(self, key: str, test=True):
        if test:
            mean = np.array([np.mean(list(map(lambda y: y[key], x))) for x in self.data])
            std = np.array([np.std(list(map(lambda y: y[key], x))) for x in self.data])
        else:
            values_with_names = [list(map(lambda y: (y[key], y["server"]["name"]), x)) for x in self.data]
            mean = np.zeros(shape=(len(values_with_names), len(REGION_NAMES)))
            std = np.zeros(shape=(len(values_with_names), len(REGION_NAMES)))
            for i, item in enumerate(values_with_names):
                values = {name: [] for name in REGION_NAMES}
                for (v, name) in item:
                    values[name].append(v)
                for name in REGION_NAMES:
                    values[name] = (np.mean(values[name]), np.std(values[name]))

                for j in range(len(REGION_NAMES)):
                    name = REGION_NAMES[j]
                    mean[i, j] = values[name][0]
                    std[i, j] = values[name][1]
            mean = pd.DataFrame(data=mean, columns=REGION_NAMES)
            std = pd.DataFrame(data=std, columns=REGION_NAMES)

        return mean, std

    def plot(self, conf):
        mean_latency, std_latency = self.__preprocess("latency")
        mean_carbon_intensity, std_carbon_intensity = self.__preprocess("carbon_intensity")
        graphs = {
            "latency": [mean_latency, std_latency],
            "carbon_intensity": [mean_carbon_intensity, std_carbon_intensity],
        }

        fig = plt.figure(figsize=(18, 14))
        x = range(self.timesteps)
        i = 0

        for key in graphs:
            [mean, std] = graphs[key]
            error = 1.96 * std / np.sqrt(len(x))

            ax = plt.subplot(2, 2, i + 1)
            ax.set_title(key)
            ax.plot(x, mean, label=key)
            ax.fill_between(x, mean - error, mean + error, alpha=0.3)
            # ax.legend()
            i += 1

        mean_servers_latency, std_servers_latency = self.__preprocess("latency", False)
        mean_servers_carbon_intensity, std_servers_carbon_intensity = self.__preprocess("carbon_intensity", False)
        graphs_servers = {
            "latency": [mean_servers_latency, std_servers_latency],
            "carbon_intensity": [mean_servers_carbon_intensity, std_servers_carbon_intensity],
        }
        for key in graphs_servers:
            [mean, std] = graphs_servers[key]
            error = 1.96 * std / np.sqrt(len(x))

            ax = plt.subplot(2, 2, i + 1)
            ax.set_title(key)
            mean.plot(kind="line", ax=ax)
            i += 1

        plt.show()
