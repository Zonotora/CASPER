import pandas as pd
import numpy as np
import os


ts = 1375315200
ts_end = 1375401600
PREFIX = r"data/na/akamai_data/ECORGeoLoad/ECORGeoLoad_"

n_rows = (ts_end - ts) // 600
idx = pd.date_range(1375315200 * 1000 ** 3, periods=n_rows, freq="10T")
t_stamps = idx.astype(np.int64) // 10 ** 9

l = []
for i in range(n_rows):
    try:
        df = pd.read_csv(f"{PREFIX}{ts+600*i}_data.dat", skiprows=[1])
    except FileNotFoundError:
        print(f"ECORGeoLoad_{ts+600*i}_data.dat did not exist!")
        l.append({})
        continue

    if df.shape[0] < 3:
        print(f"ECORGeoLoad_{ts+600*i}_data.dat did not contain any data!")
        l.append({})
        continue

    df2 = df.groupby("georegion")

    # Each country's summed 'sum_hits'
    df3 = df2["sum_hits"].sum()
    l.append(df3.to_dict())


full_df = pd.DataFrame(l)

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