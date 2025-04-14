from enum import Enum
import os
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from itertools import islice
import streamlit as st

class Lists(Enum):
    ACCEPTED_UPLOAD_FORMATS = ['LEV','COR','RAW','DEC']

class Options(Enum):
    FOLIUM_DRAW_OPTIONS = {
        "polyline": False,
        "polygon": False,
        "circle": False,
        "rectangle": False,
        "circlemarker": False,
        "marker": True 
    }

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
    

    @staticmethod
    def plot_monthly(df: pd.DataFrame):
        fig = go.Figure()

        fig.update_traces(marker_color="#0ef0d6", selector=dict(type="markers"))
        fig.update_traces(marker_symbol="x", selector=dict(mode="markers"))
        fig.add_trace(go.Scatter(
                x = df.index,
                y = df,
                mode='markers',
                name="Monthly Mean Tide Levels",
                marker=dict(symbol='x', color='#038576', size=12)
            )
        )
        fig.add_trace(go.Scatter(
                x = df.index,
                y = df,
                mode="lines",
                name="Monthly Mean Tide Levels - Plot",
                marker=dict(symbol='x', color='#038576', size=12)
            )
        )

        #add a linear regression trendline
        regression_pred, _, _ = Tools.get_linear_regression(list(range(len(df))), df)
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=regression_pred,
                mode='lines',
                name="Trendline",
                line=dict(color='grey', width=1, dash='dash')
            )
        )
        fig.update_layout(xaxis_title="Month",yaxis_title="Tide Level (cm)", showlegend=True)
        fig.update_layout(
                legend=dict(
                    orientation="h",  # Horizontal layout
                    yanchor="top",  # Anchor the legend to the top
                    y=-0.35,  # Move it below the plot
                    xanchor="center",  # Center the legend
                    x=0.5  # Center it horizontally
                )
            )
        return fig
    
    @staticmethod
    def plot_high_low(min_df: pd.DataFrame, max_df: pd.DataFrame):
        fig = go.Figure()

        fig.update_traces(marker_color="#0ef0d6", selector=dict(type="markers"))

        fig.add_trace(
            go.Scatter(
                x=min_df.index,
                y=min_df,
                mode="markers",
                name="Minimum tide observation",
                marker=dict(symbol='triangle-down', color='green', size=12)
            )
        )

        fig.add_trace(
            go.Scatter(
                x=max_df.index,
                y=max_df,
                mode="markers",
                name="Maximum tide observation",
                marker=dict(symbol='triangle-up', color='red', size=12)
            )
        )


        return fig