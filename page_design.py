import streamlit as st
import pandas as pd
import numpy as np
from appcore import ElevationParser
from local_classes.variables import Lists
import os


class AppWidgets:
    def __init__(self):    
        pass

    def upload_file_widget(self):
        parser = ElevationParser()

        with st.container(border=True):
            st.header("Upload File")
            tide_data = st.file_uploader("Choose a file",type=Lists.ACCEPTED_UPLOAD_FORMATS.value)

            if tide_data is not None:
                raw = parser.parse_upload_io(tide_data)
                st.success("File loaded!")
                return parser.parse_data_linestring(raw)
            
            else:
                st.write("Upload a valid NAMRIA tide file.")
                return None

    def app_header(self):
        with st.container(border=True):
            col1, col2 = st.columns([0.3, 0.7])
            with col1:
                st.image(os.path.join("resources","media","logo.png"), use_container_width=True)
            with col2:
                st.title("tideHunter")
                st.write("A simplified, _friendly_ interface for processing :blue[NAMRIA Tide Data]")
                st.write("_for :blue[MGBR3 - Coastal Assessment Team]_")

    def date_filter(self, dataframe: pd.DataFrame):
        st.subheader("Filter Data by Date")
        st.text("Shows only data within specified timeframe. All measurements are in centimeters. You can also download a CSV copy of the data.")
        dates = dataframe.columns

        colA, colB = st.columns([1,1])
        with colA:
            from_date = st.date_input("From", value=dates[0].date())
        with colB:
            to_date = st.date_input("To", value=dates[-1].date())

        # Convert date_input output to datetime64[ns]
        from_date = pd.to_datetime(from_date)
        to_date = pd.to_datetime(to_date)

        filtered_df = dataframe.loc[:, (dataframe.columns >= from_date)&(dataframe.columns <= to_date)]
        filtered_df.columns = [str(x.date()) for x in filtered_df]
        st.dataframe(filtered_df, height=200)

    def body(self):
        #view the body if the dataset is not empty
        self.app_header()
        dataset = self.upload_file_widget()
        if dataset:
            with st.container(border=True):
                st.subheader("Dataset Overview")
                with st.expander('Dataset View'):
                    df = pd.DataFrame.from_dict(dataset)
                    df = df.iloc[1:].replace("999",np.nan)

                    #dummy copy
                    preview = df.copy()
                    preview.columns = [str(x) for x in df.columns]

                    #update to PD DATETIME Compatible
                    df.columns = pd.to_datetime(df.columns, format='%d-%m-%Y')

                    #view
                    st.dataframe(preview,height=850)
                    st.text("You can also download a copy of the file. However your mouse to the dataframe and click the download icon.")

            with st.container(border=True):
                self.date_filter(df)
