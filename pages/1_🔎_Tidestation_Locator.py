import streamlit as st
from local_classes.variables import Lists
from page_design import TideStationLocator

def main():

    a = TideStationLocator()
    a.body()

    st.caption("Developed and designed by: _:blue[JunnieBoy13]_ ")

if __name__ == "__main__":
    main()