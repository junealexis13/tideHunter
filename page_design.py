import streamlit as st
import pandas as pd
import numpy as np
from appcore import ElevationParser
from local_classes.variables import Lists, Keys
import plotly.express as px
import os
from typing import Literal


class SingleProcessorAppWidgets:
    def __init__(self):    
        try:
            pd.set_option('future.no_silent_downcasting', True)
            self.rsmp = "ME"
        except pd._config.config.OptionError:
            print("Silent downcasting not recognized")
            self.rsmp = "M"

    def introduction(self):
        with st.container(border=True):
            st.subheader("What is Single Processor?")
            st.text("Single File Processor allows the user to create statistical inference from individual NAMRIA tide data.")

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

    def date_filter(self, dataframe: pd.DataFrame, keycode: Literal["SN","MT"]):
        dataframe = dataframe.replace(999,np.nan)
        dataframe = dataframe.sort_index(axis=1)
        st.subheader("Filter Data by Date")
        st.text("Shows only data within specified timeframe. All measurements are in centimeters. You can also download a CSV copy of the data.")
        dates = dataframe.columns

        colA, colB = st.columns([1,1])
        with colA:
            from_date = st.date_input("From", value=dates[0].date(), min_value=dates[0].date(), key=f"{keycode.lower()}_from", format="MM/DD/YYYY")
        with colB:
            to_date = st.date_input("To", value=dates[-1].date(), max_value=dates[-1].date(), key=f"{keycode.lower()}_to", format="MM/DD/YYYY")

        # Convert date_input output to datetime64[ns]
        from_date = pd.to_datetime(from_date)
        to_date = pd.to_datetime(to_date)

        filtered_df = dataframe.loc[:, (dataframe.columns >= from_date)&(dataframe.columns <= to_date)]
        filtered_df.columns = [str(x.date()) for x in filtered_df]
        st.dataframe(filtered_df, height=200)

    def monthly_hourly_average(self, dataframe: pd.DataFrame, keycode: Literal["SN","MT"]):
            # Resample to monthly frequency and calculate the mean for each hour
            monthly_hrly_avg = dataframe.T.resample(self.rsmp).mean().T
            if keycode == Keys.SINGLE.value:
                monthly_hrly_avg.columns = [x.strftime('%B') for x in monthly_hrly_avg.columns]
            else:
                monthly_hrly_avg.columns = [x.strftime('%B %y') for x in monthly_hrly_avg.columns]
                
            monthly_hrly_avg.index = [x for x in range(24)]
            st.subheader("Monthly Hourly Average Trend")
            st.text("It could be messy viewing this plot. Try doing these.")
            st.markdown('''
            * Double click toggles the Single View Mode.
            * Once in the Single View Mode, you can single click another variable to view it side-by-side
            * From Multiple View, single click the variable that you want to exclude
            * You can PAN within the plot or Zoom in and out. Perfect if you want to view a small plot portion.
            ''')
            fig = px.line(monthly_hrly_avg)
            fig.update_layout( xaxis_title="Hour",yaxis_title="Tide Level (cm)")
            st.plotly_chart(fig, theme="streamlit", use_container_width=True, key=f"{keycode.lower()}_mt_hr")

    def monthly_average(self, dataframe: pd.DataFrame, keycode: Literal["SN","MT"]):
            # Resample to monthly frequency and calculate the mean for each hour
            monthly_avg = dataframe.T.resample(self.rsmp).mean().mean(axis=1)
            if keycode == Keys.SINGLE.value:
                monthly_avg.index = [x.strftime('%B') for x in monthly_avg.index]
            else:
                monthly_avg.index = [x.strftime('%B %y') for x in monthly_avg.index]
            st.subheader("Computed Monthly Average")
            fig = px.bar(monthly_avg, x=monthly_avg.index, y=monthly_avg)
            fig.update_layout( xaxis_title="Month",yaxis_title="Tide Level (cm)")
            st.plotly_chart(fig, theme="streamlit", use_container_width=True, key=f"{keycode.lower()}_mt")

            

    def create_overview(self, dataset):
        with st.expander('Dataset View'):
            self.df = pd.DataFrame.from_dict(dataset)
            self.df = self.df.iloc[1:].replace(999,np.nan)

            #dummy copy
            preview = self.df.copy()
            preview.columns = [str(x) for x in self.df.columns]

            #update to PD DATETIME Compatible
            self.df.columns = pd.to_datetime(self.df.columns, format='%d-%m-%Y')

            #view
            st.dataframe(preview,height=850)
            st.text("You can also download a copy of the file. However your mouse to the dataframe and click the download icon.")

            
    def body(self):
        #view the body if the dataset is not empty
        self.app_header()
        self.introduction()

        dataset = self.upload_file_widget()

        if dataset:
            with st.container(border=True):
                st.subheader("Dataset Overview")
                self.create_overview(dataset=dataset)

            with st.container(border=True):
                self.monthly_hourly_average(self.df, keycode=Keys.SINGLE.value)
                
            with st.container(border=True):
                self.monthly_average(self.df, keycode=Keys.SINGLE.value)
                
            with st.container(border=True):
                self.date_filter(self.df, keycode=Keys.SINGLE.value)



class MultipleProcessorAppWidgets(SingleProcessorAppWidgets):
    def introduction(self):
        with st.container(border=True):
            st.subheader("What is Multiple Processor?")
            st.text("Multiple File Processor allows the user to upload more than 10-year data points. It enables user to create a comparative statistical analysis of tide data for different yearly tide facets.")

    def yearly_average(self, dataframe: pd.DataFrame, keycode: Literal["SN","MT"]):
        # Resample to yearly frequency and calculate the mean
        yearly_avg = dataframe.T.resample('Y').mean().mean(axis=1)
        year_data = yearly_avg.index
        yearly_avg.index = [x.year for x in year_data]

        st.subheader(f"Computed Yearly Average: {year_data[0].year} - {year_data[-1].year}")
        fig = px.scatter(yearly_avg, x=yearly_avg.index, y=yearly_avg, trendline="ols")

        #addin annot
        trendline_results = px.get_trendline_results(fig)
        if trendline_results is not None:
            trendline_params = trendline_results.px_fit_results.iloc[0].params
            slope = trendline_params[1]
            
            # Add annotation for the slope
            fig.add_annotation(
                x=0.15, y=0.85, xref="paper", yref="paper",
                text=f"Estimated annual change: {slope:.2f}cm",
                showarrow=False,
                font=dict(size=12, color="red"),
                align="center",
                bordercolor="black",
                borderwidth=1,
                borderpad=4,
                bgcolor="white",
                opacity=0.8
            )

        fig.update_traces(marker=dict(color='cyan'), selector=dict(mode='markers'))
        fig.update_traces(line=dict(color='orange', width=2, dash='dash'), selector=dict(mode='lines'))
        fig.update_layout(xaxis_title="Year", yaxis_title="Tide Level (cm)")
        st.plotly_chart(fig, theme="streamlit", use_container_width=True, key=f"{keycode.lower()}_yr")

    def upload_file_widget(self):
        parser = ElevationParser()

        with st.container(border=True):
            st.header("Upload Files (up to 10 files)")
            tide_data = st.file_uploader("Choose a file",type=Lists.ACCEPTED_UPLOAD_FORMATS.value, accept_multiple_files=True)
            

            if tide_data is not None:
                #process and merge
                merged = {}
                for data in tide_data:
                    raw = parser.parse_upload_io(data)
                    parsed = parser.parse_data_linestring(raw)
                    merged.update(parsed)
                return merged
            else:
                st.write("Upload a valid NAMRIA tide file.")
                return None

    def body(self):
        self.app_header()
        self.introduction()

        files = self.upload_file_widget()

        if files:
            with st.container(border=True):
                st.subheader("Dataset Overview")
                self.create_merged_overview(dataset=files)

            with st.container(border=True):
                self.monthly_hourly_average(self.mdf, keycode=Keys.MULTIPLE.value)
                
            with st.container(border=True):
                self.monthly_average(self.mdf, keycode=Keys.MULTIPLE.value)

            with st.container(border=True):
                self.yearly_average(self.mdf, keycode=Keys.MULTIPLE.value)
                
            with st.container(border=True):
                self.date_filter(self.mdf, keycode=Keys.MULTIPLE.value)

            

    def create_merged_overview(self, dataset):
        with st.expander('Dataset View'):
            self.mdf = pd.DataFrame.from_dict(dataset)
            self.mdf = self.mdf.iloc[1:].replace(999,np.nan)

            #dummy copy
            preview = self.mdf.copy()
            preview.columns = [str(x) for x in self.mdf.columns]

            #update to PD DATETIME Compatible
            self.mdf.columns = pd.to_datetime(self.mdf.columns, format='%d-%m-%Y')
            self.mdf = self.mdf.sort_index(axis=1)

            #view
            st.dataframe(preview,height=850)
            st.text("You can also download a copy of the file. However your mouse to the dataframe and click the download icon.")

