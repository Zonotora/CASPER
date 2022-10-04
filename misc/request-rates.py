import pandas as pd
import numpy as np
import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from casper.plot import Plot
from casper.parser import parse_arguments
from casper.util import region_names

'''

För varje stat, gör en dataframe. När du stöter på staten i akamai så appenda bara en rad.
'''

def get_ecor_region(info_df, ecor):
    ecor_row = info_df[info_df["a.ecor"] == ecor]
    country = ecor_row["b.country"].to_string()
    state = ecor_row["b.state"].to_string()
    if country in ["United States", "Canada"]:
        return state
    else:
        return country

ts = 1375315200
ts_end = 1375401600
PREFIX = r"data/na/akamai_data/ECORGeoLoad/ECORGeoLoad_"
INFO_PREFIX = r"data/na/akamai_data/ECORInfo/"

#conf = parse_arguments(["-m", "-1", "-l", "-1", "-c", "-1"])
conf = parse_arguments(["--region", "na", "-u", "30", "-t", "48", "--max-latency", "200", "--max-servers", "150", "--start-date", "2022-08-05"])
regions = region_names(conf)
print(regions)

n_rows = (ts_end - ts) // 600
idx = pd.date_range(1375315200 * 1000 ** 3, periods=n_rows, freq="10T")
t_stamps = idx.astype(np.int64) // 10 ** 9

l_from = []
l_to = []
ecor_info = {}
for i in range(n_rows):
    try:
        req_df = pd.read_csv(f"{PREFIX}{ts+600*i}_data.dat", skiprows=[1])
    except FileNotFoundError:
        print(f"ECORGeoLoad_{ts+600*i}_data.dat did not exist!")
        l_from.append({})
        continue

    try:
        info_df = pd.read_csv(f"{INFO_PREFIX}{ts+600*i}_data.dat.clean", skiprows=[1])
    except FileNotFoundError:
        print(f"ECORGeoInfo_{ts+600*i}_data.dat.clean did not exist!")
        continue

    if req_df.shape[0] < 3:
        print(f"ECORGeoLoad_{ts+600*i}_data.dat did not contain any data!")
        l_from.append({})
        continue



    # req_df.applymap(lambda x: )
    # exit()
    # print(info_df)
    #total reqs to region

    # ecor | massachussets | california

    # 1       3                  32646

    # 2

    # 3


    print(req_df)
    #to_df = req_df.groupby("ecor", as_index=False)["sum_hits"].sum()
    to_df = req_df.groupby(["ecor", "georegion"], as_index=False)["sum_hits"].sum()
    #to_df["ecor"] = to_df["ecor"].apply(lambda x: get_ecor_region(info_df, x))

    print(to_df)
    exit()
    print(to_df)
    exit()
    #total reqs from region
    to_df["ecor"] = to_df["ecor"].apply(lambda x: get_ecor_region(info_df, x))

    from_df = req_df.groupby("georegion")["sum_hits"].sum()
    l_from.append(from_df.to_dict())
    l_to.append(to_df.to_dict())

    print(l_to)
    #from is given
    exit()

    print(to_df)
    exit()




full_df = pd.DataFrame(l_from)

# Drop regions that dont really have any data
full_df = full_df.drop(
    columns=[
        "GS-South Georgia And South Sanwich-2",
        "TF-French Southern Territories-7",
        "SJ-Svalbard-3",
    ]
)

# print(full_df)
print(full_df.isna().sum())


# interpolate the missing values due to emptry files/holes in data

complete_df = full_df.interpolate(axis=0)
complete_df.insert(0, "timestamps", t_stamps)
complete_df.insert(1, "datetime", idx)

print(full_df)
print(f"Filled {full_df.isna().sum().sum()-complete_df.isna().sum().sum()} NaNs")

complete_df.to_csv(r"data/na/request_df.csv", index= False)