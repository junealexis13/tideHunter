import os, json, re
import numpy as np
from io import StringIO
from local_classes.variables import Lists
import streamlit as st
from datetime import time, datetime
import datetime

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