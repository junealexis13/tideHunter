import streamlit as st
from local_classes.variables import Lists
from page_design import TideStationLocator,SingleProcessorAppWidgets, MultipleProcessorAppWidgets, WXTideProcessor, WindroseProcessor

def main():
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Station Locator","Single Processor", "Multiple Processor", "WXTide Processor", "Windrose Processor"])
    
    with tab1:
        a = TideStationLocator()
        a.body()

    with tab2:
        b = SingleProcessorAppWidgets()
        b.body()

    with tab3:
        c = MultipleProcessorAppWidgets()
        c.body()

    with tab4:
        d = WXTideProcessor()
        d.body()

    with tab5:
        e = WindroseProcessor()
        e.body()

    st.write("Developed and designed by: _:blue[JunnieBoy13]_ ")

if __name__ == "__main__":
    main()