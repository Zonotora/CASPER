import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scheduler.util import get_regions


class Plot:
    """
    Holds data during runtime and plots it at end of simulation.
    """
    def __init__(self, conf) -> None:
        """_summary_

        Args:
            conf: Runtime configurations

        Attributes:
            region_names: Which continent to load (containing several regions)
            columns : Column labels for dataframe to simplify plotting
            data : Data for plotting, appended during runtime

        """
        self.conf = conf
        self.region_names = get_regions(conf)
        self.columns = [
            "timestep",
            "interval",
            "total_requests",
            *[f"{name}_requests_from" for name in self.region_names],
            *[f"{name}_requests_to" for name in self.region_names],
            *[f"{name}_carbon_intensity" for name in self.region_names],
            "total_carbon_emissions",
            *[f"{name}_carbon_emissions" for name in self.region_names],
            "mean_latency",
            *[f"{name}_latency" for name in self.region_names],
            "total_dropped_requests",
            *[f"{name}_dropped_requests" for name in self.region_names],
            "total_utilization",
            *[f"{name}_utilization" for name in self.region_names],
            "total_servers",
            *[f"{name}_servers" for name in self.region_names],
        ]
        self.data = []
        self.mean_latency = 0

    def add(
        self,
        server_manager,
        latency,
        carbon_intensity,
        requests_per_region,
        dropped_requests_per_region,
        t,
        interval,
        request_update_interval,
    ):
        """Adds data during runtime to data

        Args:
            server_manager: _description_
            latency: _description_
            carbon_intensity: _description_
            requests_per_region: _description_
            dropped_requests_per_region: _description_
            t: _description_
            interval: _description_
            request_update_interval: _description_
        """
        total_requests_to_region = np.sum(requests_per_region, axis=0)
        total_requests_from_region = np.sum(requests_per_region, axis=1)

        assert sum(total_requests_from_region) == sum(total_requests_to_region)

        mask = total_requests_to_region != 0

        carbon_emissions = total_requests_to_region * np.array(carbon_intensity)

        percentage = requests_per_region / (total_requests_to_region + (total_requests_to_region == 0))
        latencies = np.sum(percentage * latency, axis=0)

        capacities = server_manager.capacity_per_region() / request_update_interval
        utilization_per_region = total_requests_to_region / (capacities + (capacities == 0))

        servers_per_region = server_manager.servers_per_region()

        mean_latency = np.mean(latencies[mask])
        total_carbon_emissions = np.sum(carbon_emissions[mask])
        total_requests = np.sum(total_requests_to_region)
        total_dropped_requests = np.sum(dropped_requests_per_region)
        total_utilization = np.mean(total_requests / np.sum(capacities + (capacities == 0)))
        total_servers = np.sum(servers_per_region)

        frame = (
            t,
            interval,
            total_requests,
            *total_requests_from_region,
            *total_requests_to_region,
            *carbon_intensity,
            total_carbon_emissions,
            *carbon_emissions,
            mean_latency,
            *latencies,
            total_dropped_requests,
            *dropped_requests_per_region,
            total_utilization,
            *utilization_per_region,
            total_servers,
            *servers_per_region,
        )
        self.data.append(frame)

    def calculate_cumulative_avg_latency(self, df):
        """Gets the cumulative avg latency for ALL requests

        Args:
            df: Dataframe with request and latency data

        Returns:
            Average latency
        """
        # Total request for each timestep
        df_requests = df["total_requests"].sum()
        # Average latencies for each timestep
        df_latencies = df["mean_latency"].mean()
        # Sum of all requests
        df_all_requests = df_requests.sum()
        return np.dot(df_requests, df_latencies)/ df_all_requests


    def get(self, dt: int):
        """Return data for a timestep

        Args:
            dt: Timestep

        Returns:
            Data for a timestep
        """
        return self.data[dt]

    def build_df(self):
        """Build DataFrame from data we've gathered during runtime.

        Returns:
            Returns a dataframe with the data gathered.
        """
        return pd.DataFrame(self.data, columns=self.columns)

    def plot(self, df=None):
        """Displays region-specific data aswell as averages of regions for the plot

        Args:
            df: Data for regions. Defaults to None.
        """
        if df is None:
            df = self.build_df()
        df = df.groupby("timestep")
        fig = plt.figure(figsize=(14, 9))
        fig.tight_layout()
        fig.suptitle(
            [   "start_date: ",
                self.conf.start_date,
                "greedy_w.r.t.:",
                self.conf.type_scheduler,
                "latency:",
                self.conf.latency,
                "max_servers:",
                self.conf.max_servers,
                "server_capacity:",
                self.conf.server_capacity,
            ]
        )
        avg_latency = self.calculate_cumulative_avg_latency(df)
        print("Mean latency among all regions is: " + str(avg_latency))

        dfs = [
            df["total_requests"].sum(),
            df[[f"{name}_requests_from" for name in self.region_names]].sum(),
            df[[f"{name}_requests_to" for name in self.region_names]].sum(),
            df[[f"{name}_carbon_intensity" for name in self.region_names]].mean(),
            df["total_carbon_emissions"].sum(),
            df[[f"{name}_carbon_emissions" for name in self.region_names]].sum(),
            df["mean_latency"].mean(),
            df[[f"{name}_latency" for name in self.region_names]].mean(),
            df["total_dropped_requests"].sum(),
            df[[f"{name}_dropped_requests" for name in self.region_names]].sum(),
            df["total_utilization"].mean(),
            df[[f"{name}_utilization" for name in self.region_names]].mean(),
            df["total_servers"].mean(),
            df[[f"{name}_servers" for name in self.region_names]].mean(),
        ]
        titles = [
            "total_requests",
            "requests_from",
            "requests_to",
            "carbon_intensity",
            "total_carbon_emissions",
            "carbon_emissions",
            "mean_latency",
            "latency",
            "total_dropped",
            "dropped",
            "mean_utilization",
            "utilization",
            "total_servers",
            "servers",
        ]
        i = 0
        for df in dfs:
            ax = plt.subplot(5, 3, i + 1)
            if len(df.shape) > 1 and df.shape[1] > 0:
                ax = df.plot(ax=ax)
            else:
                ax = df.plot(ax=ax, color="black")
            ax.set_xlabel("")
            ax.set_title(titles[i])
            ax.legend().remove()
            ax.set_xticks([])
            i += 1

        fig.legend(["Mean/Total"] + self.region_names, loc="upper center", bbox_to_anchor=(0.5, 0.11), ncol=3)
        plt.show()
