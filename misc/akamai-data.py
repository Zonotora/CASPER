import pandas as pd
import numpy as np
import os
from os.path import isfile, join
from os import listdir

def main():
    ts = 1375315200
    ts_end = 1375401600
    n_rows = (ts_end - ts) // 600
    PREFIX_REQS = r"data/na/akamai_data/ECORGeoLoad/ECORGeoLoad_"
    PREFIX_INFO = r"data/na/akamai_data/ECORInfo/"


    load_server_info(PREFIX_INFO)
    load_requests(PREFIX_REQS)


def is_valid_file(file):
    return isfile(file) and ".gz" not in file

def get_region(ecor):
    pass

def load_server_info(PREFIX):
    files = [f"{PREFIX}/{f}" for f in listdir(PREFIX) if is_valid_file(join(PREFIX, f))]

    for file in files:
        info_df = pd.read_csv(file)

def load_requests(PREFIX, ecor_info):
    files = [f"{PREFIX}/{f}" for f in listdir(PREFIX) if is_valid_file(join(PREFIX, f))]

    for file in files:
        info_df = pd.read_csv(file)
        for i, row in info_df.iterrows():


def load_request_rates(PREFIX):
    files = [f"{PREFIX}/{f}" for f in listdir(PREFIX) if is_valid_file(join(PREFIX, f))]

    for file in files:
        df = pd.read_csv(file)
        for i, row in info_df.iterrows():





main()