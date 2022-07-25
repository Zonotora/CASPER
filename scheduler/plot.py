import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scheduler.constants import REGION_NAMES


class Plot:
    def __init__(self, conf) -> None:
        self.conf = conf
        self.inner_columns = [
            "timestep",
            "mean_latency",
            *[f"{name}_latency" for name in REGION_NAMES],
            "mean_carbon_emissions",
            *[f"{name}_carbon_emissions" for name in REGION_NAMES],
            "total_requests",
            *[f"{name}_requests" for name in REGION_NAMES],
        ]
        self.outer_columns = ["timestep", "servers_per_region"]
        self.inner = []
        self.outer = []

    def add(self, latency, carbon_intensity, requests_per_region, t):
        total_requests_per_region = np.sum(requests_per_region, axis=0)
        mask = total_requests_per_region != 0

        carbon_emissions = total_requests_per_region * np.array(carbon_intensity)

        percentage = requests_per_region / (total_requests_per_region + (total_requests_per_region == 0))
        latencies = np.sum(percentage * latency, axis=0)

        mean_latency = np.mean(latencies[mask])
        mean_carbon_emissions = np.mean(carbon_emissions[mask])
        total_requests = np.sum(total_requests_per_region)

        data = (
            t,
            mean_latency,
            *latencies,
            mean_carbon_emissions,
            *carbon_emissions,
            total_requests,
            *total_requests_per_region,
        )
        self.inner.append(data)

    def get(self, dt: int):
        return self.data[dt]

    def build_df(self):
        df_inner = pd.DataFrame(self.inner, columns=self.inner_columns)
        return df_inner

    def plot(self):
        df_inner = self.build_df()
        fig = plt.figure(figsize=(18, 14))
        dfs = [k
            df_inner["mean_latency"],
            df_inner[[f"{name}_latency" for name in REGION_NAMES]],
            df_inner["mean_carbon_emissions"],
            df_inner[[f"{name}_carbon_emissions" for name in REGION_NAMES]],
        ]
        i = 0
        for df in dfs:
            ax = plt.subplot(2, 2, i + 1)
            df.plot(ax=ax)
            i += 1
        plt.show()
