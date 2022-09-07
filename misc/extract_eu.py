import pandas as pd
import matplotlib.pyplot as plt

EU_CODES = [
    "AT",
    "BE",
    "BG",
    "CY",
    "CZ",
    "DE",
    "DK",
    "EE",
    "ES",
    "FI",
    "FR",
    "GR",
    "HR",
    "HU",
    "IE",
    "IT",
    "LT",
    "LU",
    "LV",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SE",
    "SI",
    "SK",
]
EUROPE_CODES = [
    "AL",
    "AD",
    "AM",
    "BY",
    "BA",
    "FO",
    "GE",
    "GI",
    "IS",
    "IM",
    "XK",
    "LI",
    "MK",
    "MD",
    "MC",
    "ME",
    "NO",
    "RU",
    "SM",
    "RS",
    "CH",
    "TR",
    "UA",
    "GB",
    "VA",
]


df = pd.read_csv("requests_all_df.csv")

eu_mask = [True if c[:2] in EU_CODES else False for c in df.columns]
df_eu = df.loc[:, eu_mask]

# Rename columns to state only
df_eu.columns = [c.split("-")[0] for c in df_eu.columns]
# Add D.C to maryland and remove D.C
# df_eu["Maryland"] += df_eu["District Of Columbia"]
# df_eu = df_eu.drop(columns=["District Of Columbia", "Other USA"])

df_eu.plot()
plt.show()
print(df_eu.describe())

df_eu.to_csv("requests_eu_df.csv")
