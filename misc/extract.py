import pandas as pd
import numpy as np

np.random.seed(1234)


def load(name):
    data = {
        "A": pd.read_csv("../api/US-CAL-CISO.csv"),
        "B": pd.read_csv("../api/US-MIDA-PJM.csv"),
        "C": pd.read_csv("../api/US-MIDW-MISO.csv"),
        "D": pd.read_csv("../api/US-TEX-ERCO.csv"),
    }
    data = {key: data[key][name] for key in data}
    df = pd.DataFrame(data=data)
    return df


def extract(name):
    df = load(name)
    df.to_csv(f"../data/{name}.csv", index=False)


def extract_with_noise(name):
    df = load(name)
    df = noise(df)
    df.to_csv(f"../data/{name}.csv", index=False)


def noise(df):
    df = df.copy()
    for col in df.columns:
        sigma = df[col].std()
        n = np.random.normal(0, sigma, len(df))
        df[col] += n
    return df


if __name__ == "__main__":
    extract_with_noise("carbon_intensity_avg")
