import pandas as pd
import pytest

from scheduler.scheduler import Scheduler
from scheduler.task import TaskBatch
from scheduler.region import Region
from scheduler.constants import REGION_NAMES, LOCATIONS


def test_carbon_greedy_day_1(df_cal, df_mida, df_midw, df_tex, servers_infty):
    max_time = 24
    data = {
        "CAL": df_cal["carbon_intensity_avg"][0:max_time],
        "MIDA": df_mida["carbon_intensity_avg"][0:max_time],
        "MIDW": df_midw["carbon_intensity_avg"][0:max_time],
        "TEX": df_tex["carbon_intensity_avg"][0:max_time],
    }
    df = pd.DataFrame(data=data)
    scheduler = Scheduler(servers_infty)
    region = Region(REGION_NAMES[0], LOCATIONS[0])

    for dt in range(max_time):
        task = TaskBatch("Task 1", 1, region)
        d = scheduler.schedule([task], dt)
        assert d["carbon_intensity"] == df.iloc[dt].min()
