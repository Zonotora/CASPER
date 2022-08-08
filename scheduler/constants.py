from numpy import deprecate


#Defines the scope of regions in continents which we use, due to data limitations and relevance
REGION_ORIGINAL = ["US-CAL-CISO", "US-MIDA-PJM", "US-MIDW-MISO", "US-TEX-ERCO"]
REGION_EUROPE = ["DE", "FR", "GB", "IE"
#, "IS"
, "IT-NO", "SE"]
REGION_NORTH_AMERICA = ["CA-ON", "CA-QC", "US-CAL-CISO", "US-MIDA-PJM", "US-NE-ISNE", "US-NW-PACW", "US-NY-NYIS"]

#Deprecated. Applied when latency was assumed linear to distance
REGION_LOCATIONS = {
    "US-CAL-CISO": (-120, 30),
    "US-MIDA-PJM": (-75, 40),
    "US-MIDW-MISO": (-80, 40),
    "US-TEX-ERCO": (-95, 30),
    "DE": (0, 0),
    "SE": (0, 0),
    "FR": (0, 0),
    "IE": (0, 0),
    "IS": (0, 0),
    "GB": (0, 0),
    "IT-NO": (0, 0),
    "US-NY-NYIS": (0, 0),
    "US-NE-ISNE": (0, 0),
    "US-NW-PACW": (0, 0),
    "CA-QC": (0, 0),
    "CA-ON": (0, 0),
}

#Regional time offsets. Offset of 0 indicates e.g. time 19:00 corresponds to 19:00 for that region.
REGION_OFFSETS = {
    "US-CAL-CISO": -7,
    "US-MIDA-PJM": -2,
    "US-MIDW-MISO": -5,
    "US-TEX-ERCO": -5,
    "DE": 2,
    "SE": 2,
    "FR": 2,
    "IE": 1,
    "IS": 0,
    "GB": 1,
    "IT-NO": 2,
    "US-NY-NYIS": -4,
    "US-NE-ISNE": -4,
    "US-NW-PACW": -5,
    "CA-QC": -4,
    "CA-ON": -4,
}
