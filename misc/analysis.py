import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("request_df.csv")

usa_mask = df.columns.str.startswith("US")
df_usa = df.loc[:, usa_mask]

# Rename columns to state only
df_usa.columns = [c.split("-")[1] for c in df_usa.columns]
# Add D.C to maryland and remove D.C
df_usa["Maryland"] += df_usa["District Of Columbia"]
df_usa = df_usa.drop(columns=["District Of Columbia", "Other USA"])

df_usa.plot()
print(df_usa.describe())

#df_usa.to_csv("requests_usa_df")
# TODO:
# Need to group countries together again, but not if in US
# Groupby column first two letters if not start with US
# Just split df into an EU and US df.


# TODO: Rename columns to US states etc..


# df.iloc[:, :25].plot()
plt.show()


#

