import matplotlib.pyplot as plt
import geopandas


# nybb = geopandas.read_file(geopandas.datasets.get_path("us"))
# world = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
# nybb.explore()
# # url of our shape file
us_states = geopandas.read_file("/home/akke/Downloads/us/cb_2018_us_state_5m.zip")
us_states.plot()
plt.show()
