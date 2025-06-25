from enum import Enum
import streamlit as st
import pandas as pd
import folium
import geopandas as gpd
import glob, os
from streamlit_folium import st_folium
#create Enum classes
class Places(Enum):
    PLACES = {
    'Bataan': [
        'Abucay',
        'Bagac',
        'City of Balanga (Capital)',
        'Dinalupihan',
        'Limay',
        'Mariveles',
        'Morong',
        'Orani',
        'Orion',
        'Pilar',
        'Samal'
    ],
    'Bulacan': [
        'Bulakan',
        'Hagonoy',
        'Paombong',
        'Obando',
        'City of Malolos (Capital)'
    ],
    'Pampanga': [
        'Lubao',
        'Macabebe',
        'Masantol',
        'Sasmuan (Sexmoan)'
    ],
    'Aurora': [
        'Baler (Capital)',
        'Casiguran',
        'Dilasag',
        'Dinalungan',
        'Dipaculao',
        'Maria Aurora',  # partly inland but may have access via river
        'San Luis',
        'Dingalan'
    ],
    'Zambales': [
        'Botolan',
        'Cabangan',
        'Candelaria',
        'Castillejos',
        'Iba (Capital)',
        'Masinloc',
        'Palauig',
        'San Antonio',
        'San Felipe',
        'San Marcelino',  # has access via Subic Bay
        'San Narciso',
        'Santa Cruz',
        'Subic',
        'Olongapo City'
    ]
}
    

class StormChase:
    def __init__(self) -> None:
        self.df = glob.glob(os.path.join("resources","geospatial","typ_1980_2024_r3.csv"))
    
    def dataset(self):
        return pd.read_csv(self.df[0])

    def __repr__(self) -> str:
        return "Dataset from Storm tracks"


class Body(StormChase):
    def __init__(self) -> None:
        super().__init__()

        self.data = self.dataset()
        self.places = Places.PLACES.value
        

    def header(self):
        with st.container(border=True):
            st.title('Typhoon Track Viewer')
            st.markdown('A simple tool to view historical typhoon tracks from International Best Track Archive for Climate Stewardship (IBTrACS) dataset.')
            st.caption('Datasets are requested from National Centers for Environmental Information - National Oceanic and Atmospheric Administration (NCEI-NOAA)')

    def get_coastal_muni(self):
        ##
        def find_province(city_or_muni, provs):
            for province, cities in provs.items():
                if city_or_muni in cities:
                    return province
            return None  
    
        ##
        muni = pd.unique(self.data['ADM3_EN'])
        prov = list(pd.unique(self.data['ADM2_EN']))

        mun, pro = st.columns([1,1])
        with mun:
            select = st.selectbox('City/Municipality',muni)
        with pro:
            prov_equi = find_province(select,self.places)
            muni_prev = st.selectbox('Province',prov,index=prov.index(prov_equi),disabled=True)
        return select, muni_prev

    def showmap(self, m, citymuni):
        shp = glob.glob(os.path.join('resources','geospatial','shapefiles',"coastal_brgy","*brgy.shp"))

        #apply filter 
        coastals = gpd.read_file(shp[0])
        coastals = coastals.loc[coastals['ADM3_EN'] == citymuni]
        coastal_bounds = coastals.total_bounds

        datetime_columns = ["date", "validOn", "validTo"]
        coastals = coastals.drop(columns=[col for col in datetime_columns if col in coastals.columns])

        
        folium.GeoJson(data=coastals.to_json(), name='Coastal_Brgy', style_function=lambda x: {"color": "violet", "weight": 0.8}).add_to(m)
        m.fit_bounds([[coastal_bounds[1], coastal_bounds[0]], [coastal_bounds[3], coastal_bounds[2]]])
        

    def fetch_storm_data(self, citymuni):
        df = self.data.loc[self.data['ADM3_EN'] == citymuni]
        return df
    
    def gen_report(self, data, m):
        #get unique storm via SID
        shp = glob.glob(os.path.join('resources','geospatial','shapefiles',"typhoon_tracks","typhoon*.shp"))
        storms = pd.unique(data['SID'])
        with st.container(border=False):
            st.subheader('Report', divider=True)

            cat, val = st.columns([.5,.5])

            typ_tracks = gpd.read_file(shp[0])
            #filter shapefile using SID
            filtered_tracks = typ_tracks[typ_tracks['SID'].isin(storms)]
            filtered_tracks.reset_index(inplace=True)
            typ_names = pd.unique(filtered_tracks['NAME'])
            nature = [
                    "_".join(x.tolist()) if len(x) > 1 else x.tolist()[0]
                    for x in [pd.unique(filtered_tracks.loc[filtered_tracks['NAME'] == name]['NATURE']) for name in typ_names]
                ]

            with cat:
                st.write('Number of Storms (1980-2024)')
                st.write('Storm Names')
            with val:
                st.write(f'{len(storms)}')
                stormNames = ""

                for i,j in zip(nature, typ_names):
                    stormNames+=f"- _:blue[{i} {j}]_\n"
                st.markdown(stormNames)

            folium.GeoJson(data=filtered_tracks.to_json(),
                        name='Storm Tracks', 
                        style_function=lambda x: {"color": "red", "weight": 1.2, "dashArray": "3, 2"},
                        popup=folium.GeoJsonPopup(
                                fields=["NAME", "NATURE", "SID"],  # 👈 customize these based on your column names
                                aliases=["Name", "Nature", "Storm ID"],  # 👈 what to show as labels
                                labels=True,
                                localize=True
                            )).add_to(m)
            
            with st.expander('View Dataset from Filter', expanded=True):
                dataView = filtered_tracks[['ISO_TIME','NAME','NATURE','USA_WIND','STORM_SPD']]
                dataView.columns = ['Storm Landfall','Int. Name','Category','Wind Speed (knots)','Storm Speed (kph)']
                st.write(dataView)
                            
    def body(self):
        #body map
        m = folium.Map(location=[15.1922672,120.7440661], zoom_start=8, tiles='esri-worldimagery')

        self.header()
        with st.form(key='view'):
            st.subheader('Parameters', divider=True)
            select = self.get_coastal_muni()
            search = st.form_submit_button('Search')
            if search:
                self.showmap(m, select[0])
                data = self.fetch_storm_data(select[0])
                self.gen_report(data=data, m=m)
                st_folium(m, use_container_width=True, height=600)

if __name__ == "__main__":
    a = Body()
    a.body()