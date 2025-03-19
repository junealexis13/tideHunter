import streamlit as st
from local_classes.variables import Lists
from page_design import TideStationLocator,SingleProcessorAppWidgets, MultipleProcessorAppWidgets

def main():
    tab1, tab2, tab3 = st.tabs(["Tide Station Locator","Single Processor", "Multiple Processor"])
    
    with tab1:
        a = TideStationLocator()
        a.body()

    with tab2:
        b = SingleProcessorAppWidgets()
        b.body()

    with tab3:
        c = MultipleProcessorAppWidgets()
        c.body()

    st.write("Developed and designed by: _:blue[JunnieBoy13]_ ")

if __name__ == "__main__":
    main()