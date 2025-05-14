import streamlit as st
from local_classes.variables import Lists
from page_design import TideStationLocator,SingleProcessorAppWidgets, MultipleProcessorAppWidgets, WXTideProcessor, WindroseProcessor

def main():


    e = WXTideProcessor()
    e.body()

    st.write("Developed and designed by: _:blue[JunnieBoy13]_ ")

if __name__ == "__main__":
    main()