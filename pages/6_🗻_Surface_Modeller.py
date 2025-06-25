import streamlit as st
import numpy as np
import pandas as pd
import pykrige
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from page_design import Modeller

#create Enum classes


def main():

    m = Modeller()
    m.body()

    st.write("Developed and designed by: _:blue[JunnieBoy13]_ ")

if __name__ == "__main__":
    main()