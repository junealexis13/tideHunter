from enum import Enum
import os
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from itertools import islice

class Lists(Enum):
    ACCEPTED_UPLOAD_FORMATS = ['LEV','COR','RAW','DEC']

class Keys(Enum):
    SINGLE = "SN"
    MULTIPLE = 'MT'

class LVL3Locations(Enum):
    Province = list(pd.unique(pd.read_csv(os.path.join("resources","geospatial","adm3_places.csv"))["ADM2_EN"]))
    City_Municipality = list(pd.unique(pd.read_csv(os.path.join("resources","geospatial","adm3_places.csv"))["ADM3_EN"]))

class CartoTileViews(Enum):
    tilesets = [
        "esri-worldimagery",
        "opentopomap",
        "openstreetmap-hot",
        "cartodb-positron",
        "esri-natgeoworldmap",
        "stadia-stamentoner",
        "stadia-stamentonerlite",
        "stadia-alidadesmoothdark"
    ]

class Tools:
    @staticmethod
    def get_linear_regression(x, y):
        '''Get the linear regression of the given x and y values'''

        x = np.array(x, dtype=np.float64)
        y = np.array(y, dtype=np.float64)
        m, b = np.polyfit(x, y, 1)

        # return y_pred
        y_pred = m * x + b
        return y_pred,m, b
    

    @staticmethod
    def calculate_distances_from_points(point_coord: tuple, prim_stations: pd.DataFrame, sec_stations: pd.DataFrame, toprank=5):
        profiles = {}

        for _, prim_st in prim_stations.iterrows():
            profiles[f"(PS) {prim_st['tidestatio']}"] = geodesic(point_coord,(prim_st['Lat'],prim_st['Long'])).km

        for _, sec_st in sec_stations.iterrows():
            profiles[f"(SS) {sec_st['namesecond']}"] = geodesic(point_coord,(sec_st['Lat'],sec_st['Long'])).km

        sorted_dict = {k:v for k, v in sorted(profiles.items(), key=lambda item: item[1], reverse=False)}
        return dict(islice(sorted_dict.items(),toprank))