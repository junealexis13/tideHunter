import os, json, re
import numpy as np
from io import StringIO, BytesIO
from local_classes.variables import Lists, Dicts
import streamlit as st
from datetime import time, datetime
import datetime
import pandas as pd


from pykrige.ok import OrdinaryKriging

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import from_origin
from rasterio.io import MemoryFile
from rasterio.crs import CRS

from plotly import graph_objects as go



class ElevationParser:
    def __init__(self):
        #constant List Values
        self.CONSTS = Lists      

    def parse_upload_io(self, upload_value):
        '''Parse Tide Dataset bytes from file. Only works with NAMRIA tide dataset'''

        # To convert to a string based IO:
        stringio = StringIO(upload_value.getvalue().decode("utf-8"))

        #read as strings
        string_data = stringio.read()

        return string_data
    

    def parse_data_linestring(self, dataset):
        '''Parse the string data representation into a compatible dataset'''

        data_collection = {}

        for line_values in dataset.strip().split("\n"):
            line_values = line_values.rstrip()
            readings = line_values[:72]
            mtd = line_values[-8:]

            #reading parser
            readings = [readings[i:i+3].strip() for i in range(0, 72, 3)]
            # Convert readings to integers, using NaN for missing values
            readings = np.array([int(r) if r.isdigit() else np.nan for r in readings])

            #mtd match
            station_id, month, day, year = [x.strip() for x in (mtd[:2], mtd[2:4], mtd[4:6], mtd[6:])]
            # st.write(station_id, month, day, year)
            # Ensure exactly 24 readings
            while len(readings) < 24:
                readings.append(np.nan)

            # Store data in dictionary
            data_collection[f"{month}-{day}-20{year}"] = {                       
                "Station_ID": station_id,
                **{f"Hour_{i}": readings[i] for i in range(24)}
            }
        return data_collection
    
class TideParser(ElevationParser):
    def __init__(self):
        pass
    
    def parse_tide_data_linestring(self, tide_txt_data):
        line = tide_txt_data.splitlines()
        station_name = line[0].strip()
        date = line[5].split(" ")[-1]
        tide_readings = [x.strip().split(" ")[:2] for x in line[5:]]
        tide_formatted = [[float(x[0]),  datetime.datetime.strptime(date+" "+x[1].strip(),"%m-%d-%Y %H:%M")] for x in tide_readings]

        return station_name, tide_formatted, date
    
class WindroseParser(ElevationParser):
    def __init__(self):
        pass

class SurfaceParser(ElevationParser):
    def __init__(self):
        pass
    
    def parse_surface_data_linestring(self, surface_data: str):
        # additional processing add here
        if not surface_data:
            return None
        else:
            return surface_data

    def interpolate_data(self, data: pd.DataFrame, resolution: int = 10):

        # Coords
        x = data['Longitude'].values
        y = data['Latitude'].values
        z = data['depth'].values

        # meshGrid creation
        gridx = np.linspace(x.min(), x.max(), resolution)
        gridy = np.linspace(y.min(), y.max(), resolution)


        # Create an Ordinary Kriging object
        OK = OrdinaryKriging(x, y, z, variogram_model='linear', verbose=False, enable_plotting=False)
        z_interp, ss = OK.execute('grid', gridx, gridy)

        return gridx, gridy, z_interp

    def raster_to_bytes(self, z_interp, gridx, gridy, projection):
        transform = from_origin(gridx[0], gridy[-1], gridx[1]-gridx[0], gridy[1]-gridy[0])
        memfile = BytesIO()
        with rasterio.MemoryFile() as mem:
            with mem.open(
                driver='GTiff',
                height=z_interp.shape[0],
                width=z_interp.shape[1],
                count=1,
                dtype='float32',
                crs=projection,  # Use appropriate CRS
                transform=transform
            ) as dataset:
                dataset.write(z_interp.astype('float32'), 1)
            memfile.write(mem.read())
        memfile.seek(0)
        return memfile

    def surface_fig(self, gridx, gridy, z_interp, fig , **kwargs):

        # colorscale from kwargs
        colorscale = kwargs.get('colorscale', 'Viridis')
        limit_padding = kwargs.get('limit_padding', 0.00)
        contour_interval = kwargs.get('contour_interval', 1.0)

        # Compute z-axis padding
        z_min = np.nanmin(z_interp)
        z_max = np.nanmax(z_interp)
        z_range = z_max - z_min
        z_pad = z_range * limit_padding

        X, Y = np.meshgrid(gridx, gridy)

        fig.add_trace(data=[go.Surface(z=z_interp, x=X, y=Y, 
                contours={
                "z": {
                    "show": True,
                    "start": np.nanmin(z_interp),
                    "end": np.nanmax(z_interp),
                    "size": contour_interval, 
                    "width": 1         # Line thickness
                }}, colorscale=colorscale)])
        fig.update_layout(title="3D Surface Model (built from  Spatial Interpolation)", scene=dict(
            xaxis_title="Long", yaxis_title="Lat", zaxis_title="Depth"
        ))

        fig.update_layout(
        title="3D Surface Model (built from Spatial Interpolation)",
        scene=dict(
            xaxis_title="Long",
            yaxis_title="Lat",
            zaxis_title="Depth",
            zaxis=dict(range=[z_min - z_pad, z_max + z_pad]),
            camera=dict(
            eye=dict(x=1.5, y=1.5, z=0.5)  # Adjust for zoom and angle
        )))

        fig.update_traces(contours_z=dict(show=True, usecolormap=True,
                                  highlightcolor="limegreen", project_z=True))

    def reproject_memfile(self, memfile: BytesIO, dst_crs: str = 'EPSG:4326') -> BytesIO:
        memfile.seek(0) #starting pointer at zero

        with MemoryFile(memfile) as src_mem:
            with src_mem.open() as src:
                src_crs = src.crs
                src_transform = src.transform
                src_data = src.read(1)
                src_height, src_width = src.shape

                #calc target transform and shape
                transform, width, height = calculate_default_transform(
                    src_crs, dst_crs, src_width, src_height,
                    *src.bounds
                )

                dst_data = np.empty((height, width), dtype=np.float32)

                # reproj the data
                reproject(
                    source=src_data,
                    destination=dst_data,
                    src_transform=src_transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear
                )

                out_memfile = BytesIO()
                with MemoryFile() as mem:
                    with mem.open(
                        driver='GTiff',
                        height=height,
                        width=width,
                        count=1,
                        dtype='float32',
                        crs=dst_crs,
                        transform=transform
                    ) as dst:
                        dst.write(dst_data, 1)
                    out_memfile.write(mem.read())
                out_memfile.seek(0)
                return out_memfile          

    def temp_save(self, rdata):
        st.session_state['raster_data_cache'] = rdata

    def validate_df(self, df: pd.DataFrame):
        '''Validate the DataFrame for surface data'''
        if df.empty:
            st.toast("The DataFrame is empty. Please upload a valid surface data file.")
            return False
        
        required_columns = ['Longitude', 'Latitude', 'depth']
        if not all(col in df.columns for col in required_columns):
            st.toast(f"The DataFrame must contain the following columns: {', '.join(required_columns)}")
            return False
        
        if df[required_columns].isnull().values.any():
            st.toast("The DataFrame contains NaN values. Performing Cleanup...")
            return False
        
        # check all rows if they have None Long, Lat, and depth
        if df[required_columns].map(lambda x: x is None).any().any():
            st.toast("The DataFrame contains None values in Longitude, Latitude, or depth columns. Performing Cleanup...")
            return False
        
        return True

    def remove_incomplete_rows(self, df: pd.DataFrame):
        '''Remove rows with NaN values in Longitude, Latitude, or depth columns'''
        if df.empty:
            return df
        else:
            return df.dropna(subset=['Longitude', 'Latitude', 'depth']).reset_index(drop=True)
        
    def remove_zero_depth_rows(self, df: pd.DataFrame):
        '''Remove rows with zero depth values'''
        if df.empty:
            return df
        else:
            return df[df['depth'] != 0].reset_index(inplace=True,drop=True)
    
    #other methodsss
    @staticmethod
    def choose_projection():
        '''Choose the projection for the surface data'''
        projections = Dicts.PROJECTIONS.value

        proj = st.selectbox(
            "Select Projection",
            projections.keys(),
            index=1,
            help="Select the projection used during the survey. (Default UTM Zone 51N)"
        )

        st.caption('Choose the projection used during the survey. This will affect how the data is displayed on the map. If unsure, use the default UTM Zone 51N.')
        return projections[proj]
    
    @staticmethod
    def choose_colorscale():
        '''Choose the colorscale for the surface data'''
        colorscales = Dicts.COLOR_PALETTES_SURFACE.value
        
        color = st.selectbox(
            "Select Colorscale",
            colorscales.keys(),
            index=0,
            help="Select the colorscale used to visualize the surface data."
        )
        st.caption("Choose a colorscale that best represents the data. ")
        return colorscales[color]
    
    @staticmethod
    def padding_percentage():
        '''Choose the limit padding for the surface data'''
        limit_padding_percentage = st.slider('Padding', min_value=0.0,
                                                 max_value=2.0,
                                                 help='Adjust the padding to normalize the surface model view.',
                                                 value=0.15)
        st.caption("Adjust the X and Y axis limits by a percentage of the data range. This helps to normalize the surface model view.")
        return limit_padding_percentage
    
    @staticmethod
    def resolution_slider():
        '''Choose the resolution for the surface data'''
        resolution = st.slider('Resolution', min_value=20, max_value=200, value=10,
                               help='Adjust the resolution of the surface model. Higher values result in finer detail but longer processing time.')
        st.caption("Adjust the resolution of the surface model. Higher values result in finer detail but longer processing time.")
        return resolution
    

    @staticmethod
    def contour_interval():
        '''Choose the contour interval for the surface data'''
        contour_interval = st.slider('Contour Interval', min_value=1.0, max_value=5.0, value=0.01, step=0.01,
                                     help='Adjust the contour interval for the surface model.')
        st.caption("Adjust the contour interval for the surface model. This affects how contours are displayed. The lower the value, the more contour lines will be displayed.")
        return contour_interval