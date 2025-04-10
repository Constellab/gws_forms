import os
import pandas as pd
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status

def display_sidebar(pmo_table : PMOTable):
    with st.sidebar:
        pmo_table.placeholder_warning_filtering = st.empty()
        st.write("**Load files**")
        with st.expander('Project plan file', icon=":material/description:"):
            # List all csv files in the saved directory
            files = sorted([f.split(".csv")[0] for f in os.listdir(
                pmo_table.folder_project_plan) if f.endswith(".csv")], reverse=True)
            cols = st.columns(2)
            options = ["Load", "Upload", "Fill manually"] if files else ["Upload", "Fill manually"]
            with cols[0]:
                pmo_table.choice_project_plan = st.selectbox("Select an option", options, key="choice_project_plan")

            # Load data
            if pmo_table.choice_project_plan == "Load":
                with cols[1]:
                    # Show a selectbox to choose one file; by default, choose the last one
                    selected_file = st.selectbox(label="Choose an existing project plan",
                                                    options=files, index=0, placeholder="Select a project plan", key="selected_file_sidebar")
                    # Load the selected file and display its contents
                    if selected_file:
                        selected_file = selected_file + ".csv"
                        file_path = os.path.join(
                            pmo_table.folder_project_plan, selected_file)
                        pmo_table.df = pd.read_csv(file_path)
            # Upload data
            # Add a file uploader to allow users to upload their project plan file
            elif pmo_table.choice_project_plan == "Upload":
                with cols[1]:
                    uploaded_file = st.file_uploader("Upload your project plan.", type=[
                                                        'csv'], key="file_uploader_sidebar")
                    if uploaded_file is not None:
                        pmo_table.df = pd.read_csv(uploaded_file)
                        pmo_table.validate_columns()
                        # Save dataframe in the folder
                        pmo_table.save_df_in_folder()
                    else:
                        st.warning('You need to upload a csv file.')
                        pmo_table.df = pmo_table.df_example
                        # Save dataframe in the folder
                        pmo_table.save_df_in_folder()
            else:
                pmo_table.df = pmo_table.df_example
                # Save dataframe in the folder
                pmo_table.save_df_in_folder()

    with st.sidebar:
        st.write("**Filtering**")
        # Filtering
        with st.expander('Filter', icon=":material/filter_alt:", expanded = True):
            st.text_input(
                label=PMOTable.NAME_COLUMN_PROJECT_NAME, placeholder=PMOTable.NAME_COLUMN_PROJECT_NAME, key = "selected_regex_filter_project_name")
            st.text_input(
                label=PMOTable.NAME_COLUMN_MISSION_NAME, placeholder=PMOTable.NAME_COLUMN_MISSION_NAME, key = "selected_regex_filter_mission_name")
            st.multiselect(label=PMOTable.NAME_COLUMN_MISSION_REFEREE,
                options=pmo_table.df[PMOTable.NAME_COLUMN_MISSION_REFEREE].unique(
                ), default=None, placeholder=PMOTable.NAME_COLUMN_MISSION_REFEREE, key = "selected_mission_referee")
            st.text_input(
                label=PMOTable.NAME_COLUMN_TEAM_MEMBERS, placeholder=PMOTable.NAME_COLUMN_TEAM_MEMBERS, key = "selected_regex_filter_team_members")
            options = pmo_table.df[PMOTable.NAME_COLUMN_STATUS].unique()
            # We want to remove "☑️ Closed" if it exists to the default options:
            default_options = [opt for opt in options if opt != Status.CLOSED.value]
            st.multiselect(label=PMOTable.NAME_COLUMN_STATUS, options=options, placeholder=PMOTable.NAME_COLUMN_STATUS, default = default_options, key = "selected_status")
            st.multiselect(label=PMOTable.NAME_COLUMN_PRIORITY, options=pmo_table.df[PMOTable.NAME_COLUMN_PRIORITY].unique(
            ), default=None, placeholder=PMOTable.NAME_COLUMN_PRIORITY, key = "selected_priority")
