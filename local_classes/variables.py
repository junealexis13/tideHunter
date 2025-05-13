from enum import Enum
import os
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from itertools import islice
import streamlit as st
import matplotlib.cm as cm

class Lists(Enum):
    ACCEPTED_UPLOAD_FORMATS = ['LEV','COR','RAW','DEC']
    ACCEPTED_UPLOAD_FORMATS_WXTIDE = ["TXT"]
    ACCEPTED_UPLOAD_FORMATS_WINDROSE = ["CSV"]

class Dicts(Enum):
    COLOR_PALETTES = {
                    'yellow-red': cm.YlOrRd,   
                    'red-green': cm.RdYlGn,
                    'cool': cm.cool,
                    'plasma': cm.plasma,
                    'inferno': cm.inferno,
                    'cividis': cm.cividis,
                    'viridis': cm.viridis
                }
    
    WIND_DIRECTION_TEMPLATE = {
            "N": (348.75, 11.25),
            "NNE": (11.25, 33.75),
            "NE": (33.75, 56.25),
            "ENE": (56.25, 78.75),
            "E": (78.75, 101.25),
            "ESE": (101.25, 123.75),
            "SE": (123.75, 146.25),
            "SSE": (146.25, 168.75),
            "S": (168.75, 191.25),
            "SSW": (191.25, 213.75),
            "SW": (213.75, 236.25),
            "WSW": (236.25, 258.75),
            "W": (258.75, 281.25),
            "WNW": (281.25, 303.75),
            "NW": (303.75, 326.25),
            "NNW": (326.25, 348.75),
        }


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

class Others(Enum):
    HTML_TEMPLATE = """
            <div style="background: linear-gradient(to right, #8e2de2, #4a00e0);
                        color: #fff;
                        margin: 2rem 1rem;
                        padding: 20px;
                        border-radius: 10px;
                        box-shadow: 5px 5px 15px rgba(0, 0, 0, 0.3);
                        font-family: 'arial', serif;
                        font-size: 2.3em;
                        font-weight: bold;
                        letter-spacing: 0.05em;
                        text-align: center;
                        overflow: hidden;
                        position: relative;">
            <span style="display: inline-block;
                        animation: shimmer 2s infinite alternate;">
                {{value}}
            </span>
            </div>

            <style>
            @keyframes shimmer {
            0% { text-shadow: -1px -1px 0 rgba(255, 255, 255, 0.2); }
            100% { text-shadow: 1px 1px 0 rgba(255, 255, 255, 0.5); }
            }
            </style>
            """

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
            profiles[f"(PS) {prim_st['tidestatio']}"] = {"distance": geodesic(point_coord, (prim_st['Lat'], prim_st['Long'])).km, "coords": [prim_st['Lat'], prim_st['Long']]}
        for _, sec_st in sec_stations.iterrows():
            profiles[f"(SS) {sec_st['namesecond']}"] = {"distance": geodesic(point_coord, (sec_st['Lat'], sec_st['Long'])).km, "coords": [sec_st['Lat'], sec_st['Long']]}

        # Fix sorting by accessing the 'distance' key in the nested dictionaries
        sorted_dict = {k: v for k, v in sorted(profiles.items(), key=lambda item: item[1]['distance'], reverse=False)}
        return dict(islice(sorted_dict.items(), toprank))
    

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