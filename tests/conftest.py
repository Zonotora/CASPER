import pytest
import pandas as pd

from scheduler.util import load
from scheduler.region import Region
from scheduler.server import Server
from scheduler.constants import REGION_NAMES, LOCATIONS


@pytest.fixture
def df_cal():
    return pd.read_csv("electricity_map/US-CAL-CISO.csv")


@pytest.fixture
def df_mida():
    return pd.read_csv("electricity_map/US-MIDA-PJM.csv")


@pytest.fixture
def df_midw():
    return pd.read_csv("electricity_map/US-MIDW-MISO.csv")


@pytest.fixture
def df_tex():
    return pd.read_csv("electricity_map/US-TEX-ERCO.csv")


@pytest.fixture
def servers_infty():
    servers = []
    for filename, location in zip(REGION_NAMES, LOCATIONS):
        df = load(f"electricity_map/{filename}.csv", False)
        r = Region(filename, location)
        s = Server(999999, r, df)
        servers.append(s)

    return servers
