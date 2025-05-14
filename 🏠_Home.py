import streamlit as st
import os

def main():
    _,hero,_ = st.columns([.25,.5,.25])
    with hero:
        st.image(os.path.join("resources","media",'logo.png'))

    st.markdown(
    ":blue-badge[:material/search: Data Analysis] " \
    ":violet-badge[:material/stacked_bar_chart: Statistics] " \
    ":green-badge[:material/waves: Tide Processing] " \
    ":orange-badge[:material/code: Automation] " \
    ":red-badge[:material/monitoring: Data Visualization] " \
    )
    
    st.title('Welcome!')
    st.write(":blue[tideHunter] is a _passion project_ created for the Coastal Hazard Assessment Team of Mines and Geosciences Bureau (MGB) Region III. Browse the sidebar to see app packages.")

    st.divider()
    st.subheader('What is this for')
    st.write('This app is intended to support the ongoing activity of the MGB III office to create useful coastal hazard maps of Barangays in Region III - Central Luzon.')

    st.divider()
    st.subheader('Where to use this app')
    st.markdown('''
        Everyone can use the app to process the following data:
        - NAMRIA Tide Data (can be requested to NAMRIA)
        - WXTide Data
        - PAG-ASA Data (limited in creating WindRose diagrams)
                
''')
    
    st.divider()
    st.caption('If you have any questions, send me an email at :blue[junealexis.santos13@gmail.com]')
    st.caption('Source code was also available at :blue[https://github.com/junealexis13/tideHunter]')
    st.caption('License under Creative Commons Non-Commercial License (CC BY-NC 4.0)')
if __name__ == "__main__":
    main()