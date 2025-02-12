import streamlit as st
from local_classes.variables import Lists
from page_design import SingleProcessorAppWidgets, MultipleProcessorAppWidgets

def main():
    tab1, tab2 = st.tabs(["Single Processor", "Multiple Processor"])

    with tab1:
        a = SingleProcessorAppWidgets()
        a.body()

    with tab2:
        b = MultipleProcessorAppWidgets()
        b.body()

    st.write("Developed and designed by: _:blue[JunnieBoy13]_ ")

if __name__ == "__main__":
    main()