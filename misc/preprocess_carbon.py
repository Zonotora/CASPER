from datetime import datetime, timezone, timedelta
import pandas as pd
import pytz
import os
import json


def basenames():
    names = []
    d = "api/files"
    for file in os.listdir(d):
        path = os.path.join(d, file)
        if os.path.isfile(path):
            base = os.path.splitext(file)[0]
            names.append(base)
    return names


# US-MIDA-PJM    {'countryName': 'USA', 'zoneName': 'PJM Interconnection, Llc'}
# DE             {'zoneName': 'Germany'}
# BR-CS          {'countryName': 'Brazil', 'zoneName': 'Central Brazil'}
# US-NY-NYIS     {'countryName': 'USA', 'zoneName': 'New York Independent System Operator'}
# SE             {'zoneName': 'Sweden'}
# FR             {'zoneName': 'France'}
# JP-KN          {'countryName': 'Japan', 'zoneName': 'Kansai'}
# UY             {'zoneName': 'Uruguay'}
# SG             {'zoneName': 'Singapore'}
# AUS-NSW        {'countryName': 'Australia', 'zoneName': 'New South Wales'}
# US-NE-ISNE     {'countryName': 'USA', 'zoneName': 'Iso New England Inc.'}
# IE             {'zoneName': 'Ireland'}
# KR             {'zoneName': 'South Korea'}
# IS             {'zoneName': 'Iceland'}
# IN-MH          {'countryName': 'India', 'zoneName': 'Maharashtra'}
# JP-TK          {'countryName': 'Japan', 'zoneName': 'Tōkyō'}
# US-CAL-CISO    {'countryName': 'USA', 'zoneName': 'California Independent System Operator'}
# US-NW-PACW     {'countryName': 'USA', 'zoneName': 'Pacificorp West'}
# CA-QC          {'countryName': 'Canada', 'zoneName': 'Québec'}
# GB             {'zoneName': 'Great Britain'}
# CA-ON          {'countryName': 'Canada', 'zoneName': 'Ontario'}
# IT-NO          {'countryName': 'Italy', 'zoneName': 'North'}

europe = {
    "DE": "Etc/GMP+2",
    "SE": "Etc/GMP+2",
    "FR": "Etc/GMP+2",
    "IE": "Etc/GMP+1",
    "IS": "Etc/GMP+0",
    "GB": "Etc/GMP+1",
    "IT-NO": "Etc/GMP+2",
}

north_america = {
    "US-MIDA-PJM": "Etc/GMP-2",
    "US-NY-NYIS": "Etc/GMP-4",
    "US-NE-ISNE": "Etc/GMP-4",
    "US-CAL-CISO": "Etc/GMP-7",
    "US-NW-PACW": "Etc/GMP-5",
    "CA-QC": "Etc/GMP-4",
    "CA-ON": "Etc/GMP-4",
}


# Copy in all the csv and place them in a folder called "files" => api/files
def paths(is_europe=True):
    d = "api/files"
    ps = []
    for file in os.listdir(d):
        path = os.path.join(d, file)
        if os.path.isfile(path):
            # only use from europe/na
            base = os.path.splitext(file)[0]
            if is_europe and base not in europe:
                continue
            if not is_europe and base not in north_america:
                continue
            ps.append((file, path))
    return ps


# Change this to generate eu/na
is_europe = False


columns = ["timestamp", "datetime", "carbon_intensity_avg"]
ps = paths(is_europe)

max_timestamp = 0
for file, path in ps:
    df = pd.read_csv(path)
    max_timestamp = max(max_timestamp, df["timestamp"][0])

date = datetime.fromtimestamp(max_timestamp, tz=timezone.utc).replace(hour=0, minute=0, second=0) + timedelta(days=1)
base_timestamp = date.timestamp()

for file, path in ps:
    df = pd.read_csv(path)
    data = []
    for index, row in df.iterrows():
        timestamp = row["timestamp"]
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(minute=0, second=0)
        timestamp = int(date.timestamp())
        if timestamp >= base_timestamp:
            data.append((timestamp, date, row["carbon_intensity_avg"]))

    df = pd.DataFrame(data, columns=columns).drop_duplicates()
    d = "europe" if is_europe else "north_america"
    df.to_csv(f"api/{d}/{file}", index=False)
