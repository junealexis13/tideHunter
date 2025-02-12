import streamlit as st
import pandas as pd
import numpy as np
from appcore import ElevationParser
from local_classes.variables import Lists
import plotly.express as px
import os


class AppWidgets:
    def __init__(self):    
        pd.set_option('future.no_silent_downcasting', True)

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
        dataframe = dataframe.replace(999,np.nan)
        st.subheader("Filter Data by Date")
        st.text("Shows only data within specified timeframe. All measurements are in centimeters. You can also download a CSV copy of the data.")
        dates = dataframe.columns

        colA, colB = st.columns([1,1])
        with colA:
            from_date = st.date_input("From", value=dates[0].date(), min_value=dates[0].date())
        with colB:
            to_date = st.date_input("To", value=dates[-1].date(), max_value=dates[-1].date())

        # Convert date_input output to datetime64[ns]
        from_date = pd.to_datetime(from_date)
        to_date = pd.to_datetime(to_date)

        filtered_df = dataframe.loc[:, (dataframe.columns >= from_date)&(dataframe.columns <= to_date)]
        filtered_df.columns = [str(x.date()) for x in filtered_df]
        st.dataframe(filtered_df, height=200)

    def monthly_hourly_average(self, dataframe: pd.DataFrame):
            # Resample to monthly frequency and calculate the mean for each hour
            monthly_hrly_avg = dataframe.T.resample('ME').mean().T
            monthly_hrly_avg.columns = [x.strftime('%B') for x in monthly_hrly_avg.columns]
            monthly_hrly_avg.index = [x for x in range(24)]
            st.subheader("Monthly Hourly Average Trend")
            fig = px.line(monthly_hrly_avg)
            fig.update_layout( xaxis_title="Hour",yaxis_title="Tide Level (cm)")
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    def monthly_average(self, dataframe: pd.DataFrame):
            # Resample to monthly frequency and calculate the mean for each hour
            monthly_avg = dataframe.T.resample('ME').mean().mean(axis=1)
            monthly_avg.index = [x.strftime('%B') for x in monthly_avg.index]
            st.subheader("Computed Monthly Average")
            fig = px.bar(monthly_avg, x=monthly_avg.index, y=monthly_avg)
            fig.update_layout( xaxis_title="Hour",yaxis_title="Tide Level (cm)")
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
            
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
                self.monthly_hourly_average(df)
                
            with st.container(border=True):
                self.monthly_average(df)
                
            with st.container(border=True):
                self.date_filter(df)
