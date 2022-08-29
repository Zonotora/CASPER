import pandas as pd

def name_translator(names):
    """Translates names from the original data source names, to our local region names

    Args:
        names: Columns of names from data we're processing

    Returns:
        Columns of the names converted to our local region names
    """
    name_translator_dic = { "US-West-N.-California" : "US-CAL-CISO",
                            "US-East-Ohio" : "US-MIDA-PJM",
                            "US-East-N.-Virginia" : "US-MIDW-MISO",
                            "US-East-N.-Virginia" : "US-TEX-ERCO",
                            "EU-Frankfurt" : "DE",
                            "EU-Paris" : "FR",
                            "EU-Ireland" : "IE",
                            "EU-Milan" : "IT-NO",
                            "EU-Stockholm" : "SE",
                            "EU-London" : "GB" }
    new_names = []
    for org_name in names:
        if org_name not in set(name_translator_dic.keys()):
            new_names.append(org_name)
            # Don't translate regions not used
            continue
        new_names.append(name_translator_dic[org_name])
    return new_names

df = pd.read_csv("api/cloudping/latency_unprocessed_50th.csv", index_col=None, header=None)
# Remove extra decimals gotten from google sheets processing
df = df.applymap(lambda x: x.replace(".00", ""))

cols = df.iloc[:, 0]
cols = name_translator(cols)
df = df.iloc[:, 1:]
# Set our local region names as new columns
df.columns = cols
# Save the file to later be loaded during the simulation
df.to_csv("api/cloudping/latency3.csv", index = False)
