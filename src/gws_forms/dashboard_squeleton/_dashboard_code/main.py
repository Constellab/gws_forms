import json
import os

import streamlit as st

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

# Streamlit app title
st.title("Squeleton AppConfig")


# Function to show content in tabs
def show_content():

    # Create tabs
    tab_1, tab_2, tab_3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

    with tab_1:
        st.write("Tab 1 ")
        st.checkbox("check me")

    with tab_2:
        st.write("Tab 2 ")

    with tab_3:
        st.write("Tab 3 ")




################################################################
logo_gencovery_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logo/logo_gencovery.png")
st.logo(logo_gencovery_path, link = "https://constellab.community/", size = "large")


st.sidebar.header("Header Sidebar")

show_content()
