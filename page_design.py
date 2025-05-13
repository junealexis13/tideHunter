import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from windrose import WindroseAxes
from appcore import ElevationParser, TideParser, WindroseParser
from streamlit_folium import st_folium
from local_classes.variables import Lists, Dicts, Keys, Tools, LVL3Locations, CartoTileViews, Options, Others

import plotly.express as px
import plotly.graph_objects as go
import os, json
import geopandas as gpd
from typing import Literal
from folium.plugins import Draw
import folium



from datetime import datetime, timedelta

class TideStationLocator:
    def __init__(self):
        #dynamically fetch the window size of device
        #removed
        if "subject_coordinates" not in st.session_state:
            st.session_state.subject_coordinates = None
        if "download_report" not in st.session_state:
            st.session_state.download_report = None
        if "folium_viewing_options" not in st.session_state:
            st.session_state.folium_viewing_options = {"expand": True}

    def app_header(self):
        with st.container(border=True):
            col1, col2 = st.columns([0.3, 0.7])
            with col1:
                st.image(os.path.join("resources","media","logo.png"), use_container_width=True)
            with col2:
                st.title("tideHunter")
                st.write("A simplified, _friendly_ interface for processing :blue[NAMRIA Tide Data]")
                st.write("_for :blue[MGBR3 - Coastal Assessment Team]_")

    def introduction(self):
        with st.container(border=True):
            st.subheader("What is Tide Station Locator?")
            st.text("Tide Station Locator, as it name suggests, locates the nearest tide station in the vicinity of a specified point.")
            st.divider()
            st.subheader(":green[_How I do it?_] :sunglasses: ")
            st.write("Geodesic distance! To calculate the geodesic distance, I basically need two coordinates. The :blue[location] and the :red[nearest tide stations].")
            st.write('''Using NAMRIA station dataset, I calculated the distance matrix from one location to many. Choose the shortest path and return the nearest. 
                     I use NAMRIA Administrative Boundary centroids as starting basepoint representing Region III cities and municipalities.''')
            st.subheader("Sample code")
            st.code('''
                    from geopy.distance import geodesic

                    # all using WGS84
                    point1 = (lat, long)

                    from station_point to manyPoints:               # calculation
                        print(geodesic(point1, station_point).km)   #calculate and prints out the distance 
                    ''')


    def station_locator(self):
        primary_ST = pd.read_csv(os.path.join("resources","geospatial","primary_stations.csv"))
        secondary_ST = pd.read_csv(os.path.join("resources","geospatial","secondary_stations.csv"))
        admin_places = pd.read_csv(os.path.join("resources","geospatial","adm3_places.csv"))

        @st.cache_data(show_spinner=False)
        def locate_map_elements():
            roads = gpd.read_file(os.path.join(os.getcwd(),"resources","geospatial","shapefiles","roads","r3_road_diss.shp"))
            boundaries = gpd.read_file(os.path.join(os.getcwd(),"resources","geospatial","shapefiles","boundaries","region_3.shp"))
            
            # Drop datetime columns from boundaries
            datetime_columns = ["date", "validOn", "validTo"]
            boundaries = boundaries.drop(columns=[col for col in datetime_columns if col in boundaries.columns])

            return (roads.to_json(), boundaries.to_json())


        with st.container(border=True):
            st.subheader("Tide Stations - PH")
            st.text("View the primary and secondary stations for the tide data.")
            
            with st.expander("Tide Stations - Philippines", expanded=False):
                st.text("Primary Stations")
                st.dataframe(primary_ST.drop(columns=["Long","Lat"], inplace=False))
                st.text("Secondary Stations")
                st.dataframe(secondary_ST.drop(columns=["Long","Lat"], inplace=False))

            with st.container(border=True):
                st.subheader("Station Locator")
                st.text("Locate the nearest station based on where the user is located. Data is based on the NAMRIA ADM3 level dataset.")
                st.caption("Take note that the geodesic distance was calculated based on the centroids of each city/municipality.")


                # settings
                with st.container(border=True):
                    st.subheader("Distance Calculation - Parameters")
                    
                    col1, col2 = st.columns([1,1])
                    with col1:
                        show_ranked = st.text_input("Show how many stations nearby",'5',max_chars=2, key="show_ranked")
                        show_roads = st.checkbox("Show Roads", value=False, key="show_roads_checkbox")
                        show_boundaries = st.checkbox("Show Boundaries", value=True, key="show_boundaries_checkbox")
                        show_drawbox = st.checkbox("Show Draw Box", value=False, key="show_drawbox_checkbox")

                    with col2:
                        #dynamically disable the place and province selectbox if drawbox is shown
                        tile_set = st.selectbox(
                            "Choose Viewing Mode",
                            CartoTileViews.tilesets.value,
                            index=3,
                            placeholder="",
                            key="folium-tileset"
                        )
                        place = st.selectbox("City/Municipality",
                                         sorted(LVL3Locations.City_Municipality.value),
                                         placeholder="Select City/Municipality",
                                         key="city_muni",
                                         disabled=show_drawbox)
                        prov = st.selectbox("Province",
                                         sorted(LVL3Locations.Province.value),
                                         placeholder="Select Province",
                                         index=2,
                                         key="province",
                                         disabled=show_drawbox)

                    st.caption("Show roads will significantly slow down the map rendering. Use with caution.")
            
            #initialize map
            m = folium.Map(location=[15.0790122,120.8849141], zoom_start=8, tiles=tile_set)
            n = folium.Map(location=[15.0790122,120.8849141], zoom_start=8, tiles=tile_set)

            with st.form(key="folium_map"):   
                fetch = st.form_submit_button("Fetch Nearest Station", help="Fetch the nearest station based on the selected city/municipality and province.")
                if fetch:
                    try:
                        #create map and add pins into it
                        if show_drawbox:
                            Draw(export=True, draw_options=Options.FOLIUM_DRAW_OPTIONS.value).add_to(m)
                            st.info("Drop a pin on the map to calculate the distance. Click again the button after setting the pin to calculate the distance.")
                        else:
                            city_data = admin_places[(admin_places["ADM3_EN"] == place) & (admin_places["ADM2_EN"] == prov)]
                            long, lat = city_data["Long"].values[0], city_data["Lat"].values[0]
                            st.session_state.subject_coordinates = (lat, long)
                            folium.Marker([lat, long], popup=f"{place}, {prov}", icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(m)
                            

                        with st.container(border=True):
                            st.subheader("Map View")
                            st.caption("If marker was enabled, you can add up to 5 points. More than it would cause leaflet to slow down.")
                                            #initialize map
                            #load shapefiles and add to map
                            with st.spinner("Loading map data. This may take awhile."):
                                roads, boundaries = locate_map_elements()

                            #shows the elements
                            if show_roads:
                                folium.GeoJson(data=roads, name="Roads", style_function=lambda x: {"color": "cyan", "weight": 0.3}).add_to(m)
                                folium.GeoJson(data=roads, name="Roads", style_function=lambda x: {"color": "cyan", "weight": 0.3}).add_to(n)
                            if show_boundaries:
                                folium.GeoJson(data=boundaries, name="Boundaries", style_function=lambda x: {"color": "yellow", "weight": 1}).add_to(m)
                                folium.GeoJson(data=boundaries, name="Boundaries", style_function=lambda x: {"color": "yellow", "weight": 1}).add_to(n)

                            for _, row in primary_ST.iterrows():
                                folium.Marker([row["Lat"], row["Long"]],
                                            popup=f"<b>{row['tidestatio']}</b><br>Lat: <i>{row['Lat']}</i> Long: <i>{row['Long']}</i><br>Station_code: <i>{row['code']}</i>",
                                            icon=folium.Icon(color="green", icon="tower-observation", prefix="fa")).add_to(m)
                                folium.Marker([row["Lat"], row["Long"]],
                                            popup=f"<b>{row['tidestatio']}</b><br>Lat: <i>{row['Lat']}</i> Long: <i>{row['Long']}</i><br>Station_code: <i>{row['code']}</i>",
                                            icon=folium.Icon(color="green", icon="tower-observation", prefix="fa")).add_to(n)

                            for _, row in secondary_ST.iterrows():
                                folium.Marker([row["Lat"], row["Long"]],
                                            popup=f"<b>{row['namesecond']}</b><br>Lat: <i>{row['Lat']}</i> Long: <i>{row['Long']}</i>",
                                            icon=folium.Icon(color="orange", icon="tower-observation", prefix="fa")).add_to(m)
                                folium.Marker([row["Lat"], row["Long"]],
                                            popup=f"<b>{row['namesecond']}</b><br>Lat: <i>{row['Lat']}</i> Long: <i>{row['Long']}</i>",
                                            icon=folium.Icon(color="orange", icon="tower-observation", prefix="fa")).add_to(n)
                            
                        with st.expander('Viewfinder',expanded=st.session_state.folium_viewing_options['expand']):
                            fol_map = st_folium(m,use_container_width=True, height=350)

                        with st.container(border=True):
                            if not show_drawbox:
                                st.subheader(f"Tide Station: {place}, {prov}",divider=True)
                                near_st = Tools.calculate_distances_from_points(st.session_state.subject_coordinates, primary_ST, secondary_ST, int(show_ranked))
                                st.session_state.download_report = near_st
                                for i, (k, v) in enumerate(near_st.items()):
                                    st.write(f"**Distance to :blue[_{k}_]** :green[_{round(v['distance'], 4)} km_]")
                                    if i == 0:
                                        lcolor = 'green'
                                        lweight = 2.5
                                        dash_array = None
                                    else:
                                        lcolor = 'grey'
                                        lweight = 0.5
                                        dash_array = "5, 5"
                                    
                                    folium.PolyLine(locations=[(lat,long),(v['coords'][0],v['coords'][1])],popup=f"Dist to {k}: {round(v['distance'],4)}km",color=lcolor, weight=lweight,opacity=1,dash_array=dash_array).add_to(n)
                                    folium.Marker([lat, long], popup=f"{place}, {prov}", icon=folium.Icon(color="blue", icon="flag", prefix="fa")).add_to(n)
                                st.subheader('Distance Preview',divider=True)
                                st.caption('The thickest green line represents the closest station. You can also click on line to view distance popup.')
                                st_folium(n,use_container_width=True, height=600)

                            elif show_drawbox:
                                poi = fol_map['all_drawings']
                                if poi is not None:
                                    #contract original viewfinder in pin assignment mode
                                    for i, point in enumerate(poi):
                                        with st.container(border=False):
                                            st.subheader(f"Point {i+1}",divider=True)
                                            if point["geometry"]["type"] == "Point":
                                                lat, long = point["geometry"]["coordinates"][1], point["geometry"]["coordinates"][0]
                                                folium.Marker([lat, long], popup=f"{place}, {prov}", icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(n)
                                                st.session_state.subject_coordinates = (lat, long)
                                                near_st = Tools.calculate_distances_from_points(st.session_state.subject_coordinates, primary_ST, secondary_ST, int(show_ranked))
                                                st.session_state.download_report = near_st
                                                for i,(k, v) in enumerate(near_st.items()):
                                                    st.write(f"**Distance to :blue[_{k}_]** :green[_{round(v['distance'], 4)} km_]")
                                                    if i == 0:
                                                        lcolor = 'green'
                                                        lweight = 2.5
                                                        dash_array = None
                                                    else:
                                                        lcolor = 'grey'
                                                        lweight = 0.5
                                                        dash_array = "5, 5"
                                                    folium.PolyLine(locations=[(lat,long),(v['coords'][0],v['coords'][1])],popup=f"Dist to {k}: {round(v['distance'],4)}km",color=lcolor, weight=lweight,opacity=1,dash_array=dash_array).add_to(n)
                                                st.divider()
                                    st.subheader('Distance Preview',divider=True)
                                    st.caption('The thickest green line represents the closest station. You can also click on line to view distance popup.')
                                    st_folium(n,use_container_width=True, height=600)


                    except IndexError:
                        st.error(f"Error location. There is no place like **{place}**, **{prov}** :face_with_one_eyebrow_raised:")
                        
        download_contents = st.download_button(
            "Download summary of report",
            data=json.dumps(st.session_state.download_report, indent=4),
            file_name="nearby_stations.txt",
            mime="text/plain")

    def body(self):
        #view the body if the dataset is not empty
        self.app_header()
        self.introduction()
        self.station_locator()

class SingleProcessorAppWidgets:
    def __init__(self):    
        try:
            pd.set_option('future.no_silent_downcasting', True)
            self.rsmp = "ME"
        except pd._config.config.OptionError:
            print("Silent downcasting not recognized")
            self.rsmp = "M"
        self.filename = None

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
                self.filename = tide_data.name
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

        return monthly_hrly_avg

    def monthly_average(self, dataframe: pd.DataFrame, keycode: Literal["SN","MT"]):
        # Resample to monthly frequency and calculate the mean for each hour
        monthly_avg = dataframe.T.resample(self.rsmp).mean().mean(axis=1)
        max_monthly_tide = dataframe.T.resample(self.rsmp).max().max(axis=1)
        min_monthly_tide = dataframe.T.resample(self.rsmp).min().min(axis=1)

        if keycode == Keys.SINGLE.value:
            monthly_avg.index = [x.strftime('%B') for x in monthly_avg.index]
            max_monthly_tide.index = [x.strftime('%B') for x in max_monthly_tide.index]
            min_monthly_tide.index = [x.strftime('%B') for x in min_monthly_tide.index]
        else:
            monthly_avg.index = [x.strftime('%B %y') for x in monthly_avg.index]
            max_monthly_tide.index = [x.strftime('%B %y') for x in max_monthly_tide.index]
            min_monthly_tide.index = [x.strftime('%B %y') for x in min_monthly_tide.index]


        st.subheader("Computed Monthly Average")
        graph_obj = Tools.plot_monthly(monthly_avg)
        st.plotly_chart(graph_obj, theme="streamlit", use_container_width=True, key=f"{keycode.lower()}_mt")


        st.subheader("Range Values")
        graph_obj_minmax = Tools.plot_high_low(min_df=min_monthly_tide, max_df=max_monthly_tide)
        st.plotly_chart(graph_obj_minmax, theme="streamlit", use_container_width=True, key=f"{keycode.lower()}_minmax")

        #feed to next req
        monthly_avg, slope, intercept = Tools.get_linear_regression(list(range(len(monthly_avg))), monthly_avg)
        return monthly_avg, slope, intercept

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

    def generate_report(self, monthly_avg: pd.Series, monthly_hrly_avg, slope, intercept):
        if isinstance(monthly_avg, pd.Series):
            annual_avg_values = monthly_avg.mean()
        else:
            annual_avg_values = monthly_avg[0].mean()

        st.header("Tide Report")
        st.text("Generate a summary report of the tide data.")
        st.divider()

        dataset = {
            "Annual Tide Average": f"{annual_avg_values:.2f}cm",
            "Mean Rate of Change": f"{slope:.3f}cm",
            "Equation of the line": f"y={slope:.3f}x + {intercept:.3f}"
        }

        st.table(pd.DataFrame(dataset, index=[self.filename.split(".")[0]]))

        filename = self.filename.split(".")[0]
        download_button = st.download_button("Download a .txt summary copy",
                                            f"Monthly Tide Average: {annual_avg_values:.2f}cm\n"
                                            f"Mean Rate of Change: {slope:.3f}cm\n"
                                            f"Equation of the line: y={slope:.3f}x + {intercept:.3f}",
                                            f"tide_report_{filename}.txt",
            key="gen_report_monthly"
        )
        if download_button:
            st.success("Report downloaded!")

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
                hourlyAvg = self.monthly_hourly_average(self.df, keycode=Keys.SINGLE.value)
            with st.container(border=True):
                monthlyAvg, slope, intercept = self.monthly_average(self.df, keycode=Keys.SINGLE.value)
            with st.container(border=True):
                self.generate_report(monthlyAvg, hourlyAvg, slope, intercept)
            with st.container(border=True):
                self.date_filter(self.df, keycode=Keys.SINGLE.value)

class MultipleProcessorAppWidgets(SingleProcessorAppWidgets):
    def introduction(self):
        with st.container(border=True):
            st.subheader("What is Multiple Processor?")
            st.text("Multiple File Processor allows the user to upload more than 10-year data points. It enables user to create a comparative statistical analysis of tide data for different yearly tide facets.")

    def yearly_average(self, dataframe: pd.DataFrame, keycode: Literal["SN","MT"]):
        # Resample to yearly frequency and calculate the mean
        try:
            resamp_code = "YE"
            yearly_avg = dataframe.T.resample(resamp_code).mean().mean(axis=1)
        except ValueError:
            resamp_code = "Y"
            yearly_avg = dataframe.T.resample(resamp_code).mean().mean(axis=1)

        year_data = yearly_avg.index
        yearly_avg.index = [x.year for x in year_data]

        # Calculate the maximum annual tide
        max_annual_tide = dataframe.T.resample(resamp_code).max().max(axis=1)
        max_annual_tide.index = [x.year for x in max_annual_tide.index]

        # Calculate another mean annual tide (e.g., median)
        min_annual_tide = dataframe.T.resample(resamp_code).min().min(axis=1)
        min_annual_tide.index = [x.year for x in min_annual_tide.index]


        st.subheader(f"Computed Yearly Average: {year_data[0].year} - {year_data[-1].year}")
        fig = px.scatter(yearly_avg, x=yearly_avg.index, y=yearly_avg, trendline="ols")

        fig.update_traces(marker=dict(color='grey'), selector=dict(mode='markers'))
        fig.update_traces(line=dict(color='orange', width=2, dash='dash'), selector=dict(mode='lines'))
        fig.update_layout(xaxis_title="Year", yaxis_title="Tide Level (cm)")

        fig.add_trace(go.Scatter(
            x=max_annual_tide.index, 
            y=max_annual_tide, 
            mode='markers', 
            name='Max Annual Tide Level', 
            marker=dict(symbol='line-ew-open', color='red',line_width=5, size=8) 
        ))

        # Add scatter plot with small horizontal line markers for min tide
        fig.add_trace(go.Scatter(
            x=min_annual_tide.index, 
            y=min_annual_tide, 
            mode='markers', 
            name='Min Annual Tide Level', 
            marker=dict(symbol='line-ew-open', color='blue',line_width=5, size=8)
        ))

        st.plotly_chart(fig, theme="streamlit", use_container_width=True, key=f"{keycode.lower()}_yr")
        
        y,m,b = Tools.get_linear_regression(list(range(len(yearly_avg))), yearly_avg)
        return yearly_avg, y,m,b

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
            
    def generate_report_yr(self, yearly_avg: pd.Series, slope, intercept):
        if isinstance(yearly_avg, pd.Series):
            annual_avg_values = yearly_avg.mean().mean()
        else:
            annual_avg_values = yearly_avg.mean().mean()

        st.header("Tide Report")
        st.text("Generate a summary report of the tide data.")
        st.divider()

        dataset = {
            "Annual Tide Average": f"{annual_avg_values:.2f}cm",
            "Mean Rate of Change": f"{slope:.3f}cm",
            "Equation of the line": f"y={slope:.3f}x + {intercept:.3f}"
        }

        
        st.table(pd.DataFrame(dataset,index=["Summary"]))

        filename = f"{yearly_avg.index.min()}-{yearly_avg.index.max()}"
        st.divider()
        color = "green" if slope < 0 else "red"
        remarks = "rising" if slope > 0 else "decreasing"
        st.write(f"Tide level is generally **:{color}[{remarks}]**.")
        download_button = st.download_button("Download a .txt summary copy",
                                            f"Monthly Tide Average: {annual_avg_values:.2f}cm\n"
                                            f"Mean Rate of Change: {slope:.3f}cm\n"
                                            f"Equation of the line: y={slope:.3f}x + {intercept:.3f}",
                                            f"tide_report_{filename}.txt",
            key="gen_report_monthly"
        )

        if download_button:
            st.success("Report downloaded!")

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
                yrly_pred, slope, intercept = self.monthly_average(self.mdf, keycode=Keys.MULTIPLE.value)

            with st.container(border=True):
                try:
                    pred, y, m, b = self.yearly_average(self.mdf, keycode=Keys.MULTIPLE.value)
                except (AttributeError, np.linalg.LinAlgError):
                    st.error("Not enough points to create a regression calculation. Consider uploading additional points.")

            with st.container(border=True):
                try:
                    # regression_pred, slope, intercpt = Tools.get_linear_regression(list(range(len(self.mdf))), self.mdf)
                    self.generate_report_yr(pred, slope, intercept)
                except UnboundLocalError:
                    pass
        
            with st.container(border=True):
                try:
                    self.date_filter(self.mdf, keycode=Keys.MULTIPLE.value)
                except UnboundLocalError:
                    pass

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

class WXTideProcessor(SingleProcessorAppWidgets):
    def introduction(self):
        with st.container(border=True):
            st.subheader("What is WXTide Processor?")
            st.text("WXTide Processor allows the user to create statistical inference derived from synthesized tide data from WXTide Platform. For more information, visit http://wxtide32.com/")

    def upload_file_widget(self):
        parser = TideParser()

        with st.container(border=True):
            st.header("Upload File")
            tide_data = st.file_uploader("Choose a file",type=Lists.ACCEPTED_UPLOAD_FORMATS_WXTIDE.value, key="wxtide_upload")

            if tide_data is not None:
                raw = parser.parse_upload_io(tide_data)
                self.filename = tide_data.name
                st.success("File loaded!")
                return parser.parse_tide_data_linestring(raw)
            
            else:
                st.write("Upload a valid WXTide TXT tide file.")
                return None
            

    def plot_tide(self, dataset):
        station = dataset[0]
        data = [val for (val,_) in dataset[1]]
        dates = [date for (_,date) in dataset[1]]
        date_fetched = dataset[2]

        #create a dataframe and plot in plotly
        df = pd.DataFrame(data, columns=["Tide Level"])
        df["TimeUnit"] = pd.to_datetime(dates, format="%d-%m-%Y %H:%M")

        #plot using plotly go

        fig = go.Figure()

        with st.container(border=True):
            st.subheader(f"{station} ({date_fetched})", divider=True)
            st.text("This plot is interactive. You can zoom in and out. You can also hover over the plot to view the data.")

            fig.add_trace(go.Scatter(x=df["TimeUnit"], y=df["Tide Level"], mode='lines', name=station))
            st.plotly_chart(fig, theme="streamlit", use_container_width=True, key="wxtide_plot")

        return df
    

    def calculate_mean_tide(self, dataframe):
        with st.container(border=True):
            st.subheader('Calculation Parameters', divider=True)
            st.caption("Calculate the mean tide level based on the selected timeframe. The time unit is in minutes. But it depends on the data provided.")
            st.caption("E.g. If you uploaded every 5 minutes, the plot will only show values per 5 minutes.")

            # conver the time unit to datetime compatible with streamlit - it prefer pythondt.dt
            dataframe['TimeUnit'] = pd.to_datetime(dataframe['TimeUnit'], format="%H:%M")
            data = dataframe["TimeUnit"]
            dataframe['FormattedDT'] = [x.to_pydatetime().time() for x in data]

            #calculate the mean tide level
            from_, to_ = st.columns([1,1])
            with from_:
                fromTime = st.time_input("From",
                                        value=dataframe['FormattedDT'].min(), 
                                        key="wxtide_from",
                                        step=timedelta(minutes=1))
            with to_:
                toTime = st.time_input("To", 
                                       value=dataframe['FormattedDT'].max(),
                                       key="wxtide_to",
                                       step=timedelta(minutes=1))

            #filter the data
            filtered_data = dataframe.loc[(dataframe['FormattedDT']>= fromTime) & (dataframe['FormattedDT'] <= toTime)]
            survey_mean = filtered_data['Tide Level'].mean()
            daily_mean = dataframe['Tide Level'].mean()

            st.caption(f"Number of samples: {len(filtered_data)}")

        with st.container(border=True):
            st.subheader("Tide Level during the Survey")
            st.caption('Specific mean tide value calculated from set time interval.')
            st.markdown(Others.HTML_TEMPLATE.value.replace("{{value}}", str(round(survey_mean, 4))+"m"), unsafe_allow_html=True)

        with st.container(border=True):
            st.subheader("Mean Tide Level")
            st.caption('Mean tide level for the whole day.')
            st.markdown(Others.HTML_TEMPLATE.value.replace("{{value}}", str(round(daily_mean, 4))+"m"), unsafe_allow_html=True)

    def body(self):
        self.app_header()
        self.introduction()
        dataset = self.upload_file_widget()

        if dataset:
            df = self.plot_tide(dataset)
            get_mean = self.calculate_mean_tide(df)

class WindroseProcessor(SingleProcessorAppWidgets):
    def introduction(self):
        with st.container(border=True):
            st.subheader("What is Windrose Processor?")
            st.text("Windrose Processor allows the user to create statistical inference derived from wind data from PAG-ASA.")
            st.caption("For more information, visit https://bagong.pagasa.dost.gov.ph/")

    def deg_to_compass(self, degree):
        if not pd.isna(degree):
            directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                        'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
            index = int((degree % 360) / 22.5 + 0.5)
            return directions[index % 16]
        else:
            return np.nan

    def upload_file_widget(self):
        parser = WindroseParser()

        with st.container(border=True):
            st.header("Upload File")
            tide_data = st.file_uploader("Choose a file",type=Lists.ACCEPTED_UPLOAD_FORMATS_WINDROSE.value, key="windrose_upload")

            if tide_data is not None:
                #create an empty dataframe
                new_df = pd.DataFrame()

                #parse the data
                raw = pd.read_csv(tide_data)

                #create a dateobject by merging 2 columns of Year and Month
                new_df["Date"] = pd.to_datetime(raw["YEAR"].astype(str) + "-" + raw["MONTH"].astype(str), format="%Y-%m")
                new_df["STRDate"] = new_df["Date"].dt.strftime("%Y-%B")
                new_df["WindSpeed"] = raw["WIND_SPEED"].replace(-999, np.nan)
                new_df["WindDirection"] = raw["WIND_DIRECTION"].replace(-999, np.nan)

                new_df['WindDirectionDesc'] = new_df["WindDirection"].apply(self.deg_to_compass)
                
                #create a col where it indicates where the wind is blowing to
                new_df['WindDirectionTo'] = (new_df['WindDirection'] + 180) % 360
                return new_df
            
            else:
                st.write("Upload a valid wind data in CSV tide file.")
                return None
            

    def plot_windrose(self, dataset: pd.DataFrame, date_range = None, bg='#000000', cpl='viridis'):
        #create a fig first
        fig = plt.figure(figsize=(12,6))
        
        #apply customizations
        fig.patch.set_facecolor(bg)  
        colorMap = Dicts.COLOR_PALETTES.value[cpl]

        #pre-clean df
        df = dataset.replace(-999,np.nan)

        if date_range:
            df = df.loc[(df['Date'] > date_range[0]) & (df['Date'] < date_range[1])  ]
        
        #init windrose
        ax = WindroseAxes.from_ax(fig=fig)

        #set
        ax.bar(df['WindDirectionTo'], df['WindSpeed'], normed=True, cmap=colorMap)
        ax.set_legend(
            title='Wind Speed (m/s)',
            title_fontsize=8
        )
        return st.pyplot(fig)
    
    def calculate_wind_resultant(self, dataset: pd.DataFrame, date_range = None):
        df = dataset.replace(-999,np.nan)
        if date_range:
            df = df.loc[(df['Date'] > date_range[0]) & (df['Date'] < date_range[1])  ]

        radians = np.deg2rad(df['WindDirectionTo'])

        #standard physicals components to calculate u and v components [its easier to implement component method that tail-to-tip]
        df['u'] = df['WindSpeed'] * np.cos(radians)
        df['v'] = df['WindSpeed'] * np.sin(radians)

        u_avg = df['u'].mean()
        v_avg = df['v'].mean()

        resultant_magnitude = np.sqrt(u_avg**2 + v_avg**2)
        resultant_direction = (np.arctan2(v_avg, u_avg) * 180 / np.pi) % 360

        with st.container(border=True):
            st.html(f'''
                <div style="
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    max-width: 500px;
                    margin: auto;
                    font-family: 'Segoe UI', sans-serif;
                ">
                    <h2 style="color: #ffffff;"> Resultant Wind Vector</h2>
                    <p style="font-size: 1rem; margin: 0.2rem;">Magnitude: <span style="color: #00DFFF;"><b>{round(resultant_magnitude,2)}m/s</b></span></p>
                    <p style="font-size: 1rem; margin: 0.2rem;">Direction (to): <span style="color: #FFFD00;"><b>{round(resultant_direction,2)}° </b>- Blow towards {self.describe_wind_direction(resultant_direction)}</span></p>
                </div>
                ''')

    def plot_windrose_widget(self, dataset):
        with st.container(border=True):
            st.subheader('Generate a Windrose diagram',divider=True)
            st.caption('Take note that the Wind Rose generated indicates where it was blowing to. The metadata from DOST PAG-ASA indicates that the column reflects where the wind is blowing from. I changed it into where it was blowing to.')

            #create a parameter dashboard
            with st.container(border=True):
                    st.text('View settings')
                    st.caption("Let's you tweak what the windrose plotter is going to show. Select date will only enable the date you want to plot. Background color changes the plot face color and the palette changes the rose colors.")
                    date_slider = st.select_slider("Select Date",
                                                   options=dataset.Date,
                                                   value=(dataset.Date.min(), dataset.Date.max()))        
                    col1, col2 = st.columns((1,1))
                    with col1:
                        background_color = st.color_picker('Background Color',value="#ffffff")
                    with col2:
                        color_palette = st.selectbox('Choose Palette',Dicts.COLOR_PALETTES.value.keys(), 3)
           
            gen = st.button(label="Create",key='windrose-generate')
            if gen:
                self.plot_windrose(dataset, date_range=date_slider, bg=background_color, cpl=color_palette)
                self.calculate_wind_resultant(dataset, date_range=date_slider)

    def describe_wind_direction(self, angle):
        #match direction #could still be changed
        for direction, angle_range in Dicts.WIND_DIRECTION_TEMPLATE.value.items():
            if angle_range[0] <= angle < angle_range[1] or (direction == 'N' and angle >= angle_range[0] or angle < angle_range[1]):
                return direction
        
    def body(self):
        self.app_header()
        self.introduction()
        dataset = self.upload_file_widget()

        if dataset is not None and isinstance(dataset, pd.DataFrame):
            self.plot_windrose_widget(dataset)
            
