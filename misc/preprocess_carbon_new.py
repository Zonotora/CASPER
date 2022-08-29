from turtle import forward
import pandas as pd
import numpy as np

provider = "azure"
path = "api\\azure\\"
#na_regions = ["Arizona", "California", "Illinois", "Iowa", "Ontario", "Texas", "Virginia", "Washington", "Wyoming", "Quebec"]
# Order important, do not change
na_regions = ["Iowa", "Virginia", "Virginia", "Illinois", "Texas", "Wyoming", "California", "Washington", "Arizona", "Ontario", "Quebec"]

#Regional info
df = pd.read_json(path + "cloud_regions.full.json")
df = df[df["provider"] == provider]
df = df[df["name"].isin(na_regions)]

#Read carbon info
dfs = [pd.read_csv(path + "us\\" + provider + "-" + region_code + "-" + "series.csv", index_col = False) for region_code in df["code"]]

for df, region in zip(dfs, na_regions):

    df = df[[
        #"timestamp",
        "zone_datetime", "zone_carbon_intensity_avg"]]
    df.columns = [
        #"timestamp",
        "datetime", "carbon_intensity_avg"]
    if region not in {"California","Ontario"}:
        df.drop(df.head(1).index,inplace=True)
    if region == "California":
        df.drop(df.tail(2).index,inplace=True)
    if region == "Ontario":
        df.drop(df.tail(2).index,inplace=True)

    if df.shape[0]% 2 != 0:
        first_row = pd.DataFrame([df.iloc[0]])
        df = pd.concat([first_row, df], ignore_index= True)

    df.loc[:,"datetime"] = pd.to_datetime(df["datetime"])
    df = df.resample('H', on= "datetime").mean()
    df.insert(loc=0, column="datetime", value= df.index)

    df["carbon_intensity_avg"] = df["carbon_intensity_avg"].interpolate(
        method ='linear', axis = 0, direction = "forward")

    timestamps = df.datetime.values.astype(np.int64) // 10 ** 9
    df.insert(loc=0, column="timestamps", value= timestamps)

    df.to_csv(f"api\\north_america\\{region}.csv", index=False)
