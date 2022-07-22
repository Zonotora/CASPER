import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scheduler.constants import REGION_NAMES


class Plot:
    def __init__(self, conf, data=None) -> None:
        self.conf = conf
        self.timesteps = conf.timesteps
        if data is None:
            self.data = [[] for _ in range(conf.timesteps)]
        else:
            self.data = data

    def add(self, scheduled_item, t):
        data = {}
        for key in ["latency", "carbon_emissions"]:
            data[key] = scheduled_item[key]

        # s = scheduled_item["server"]
        # data["server"] = {"name": s.region.name, "utilization": s.current_utilization}

        self.data[t].append(data)

    def get(self, dt: int):
        return self.data[dt]

    def __preprocess(self, key: str, all=True, should_index_server=False):
        def index_server(y, key, should_index_server=False):
            if should_index_server:
                return y["server"][key]
            return y[key]

        if all:
            mean = np.array(
                [np.mean(list(map(lambda y: index_server(y, key, should_index_server), x))) for x in self.data]
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
                    if len(values[name]) == 0:
                        values[name] = (0, 0)
                    else:
                        values[name] = (np.mean(values[name]), np.std(values[name]))

                for j in range(len(REGION_NAMES)):
                    name = REGION_NAMES[j]
                    mean[i, j] = values[name][0]
                    std[i, j] = values[name][1]
            mean = pd.DataFrame(data=mean, columns=REGION_NAMES)
            std = pd.DataFrame(data=std, columns=REGION_NAMES)

        return mean, std

    def plot(self):
        mean_latency, std_latency = self.__preprocess("latency")
        mean_carbon_emissions, std_carbon_emissions = self.__preprocess("carbon_emissions")
        # mean_utilization, std_utilization = self.__preprocess("utilization", should_index_server=True)
        graphs = {
            "latency": [mean_latency, std_latency],
            "carbon_emissions": [mean_carbon_emissions, std_carbon_emissions],
            # "utilization": [mean_utilization, std_utilization],
        }

        fig = plt.figure(figsize=(18, 14))
        x = range(self.timesteps)
        i = 0

        for key in graphs:
            [mean, std] = graphs[key]
            error = 1.96 * std / np.sqrt(len(x))

            ax = plt.subplot(2, 3, i + 1)
            ax.set_title(key)
            ax.plot(x, mean, label=key)
            ax.fill_between(x, mean - error, mean + error, alpha=0.3)
            i += 1
        plt.show()
        exit()
        # TODO: Make sure this work
        mean_servers_latency, std_servers_latency = self.__preprocess("latency", False)
        mean_servers_carbon_emissions, std_servers_carbon_emissions = self.__preprocess("carbon_emissions", False)
        mean_servers_utilization, std_servers_utilization = self.__preprocess(
            "utilization", False, should_index_server=True
        )
        graphs_servers = {
            "latency": [mean_servers_latency, std_servers_latency],
            "carbon_emissions": [mean_servers_carbon_emissions, std_servers_carbon_emissions],
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
