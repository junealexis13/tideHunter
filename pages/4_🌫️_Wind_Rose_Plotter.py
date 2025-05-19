import streamlit as st
from local_classes.variables import Lists
from page_design import WindroseProcessor

def main():

    e = WindroseProcessor()
    e.body()

    st.write("Developed and designed by: _:blue[JunnieBoy13]_ ")

if __name__ == "__main__":
    main()