import json
import os
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status

def display_sidebar(pmo_table : PMOTable):
    pmo_table.pmo_state.get_df_to_save()
    pmo_table.pmo_state.get_active_project_plan(pmo_table.df)

    with st.sidebar:
        pmo_table.placeholder_warning_filtering = st.empty()
        st.write("**Load files**")
        with st.expander('Project plan file', icon=":material/description:"):
            # List all csv files in the saved directory
            files = sorted([f.split(".csv")[0] for f in os.listdir(
                pmo_table.folder_project_plan) if f.endswith(".csv")], reverse=True)
            cols = st.columns(2)
            if files:
                with cols[0]:
                    pmo_table.choice_project_plan = st.selectbox("Select an option", [
                                                            "Load", "Upload", "Fill manually"], key="choice_project_plan")
            else:
                with cols[0]:
                    pmo_table.choice_project_plan = st.selectbox("Select an option", [
                                                            "Upload", "Fill manually"], key="choice_project_plan_sidebar")

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
                        pmo_table.pmo_state.set_active_project_plan(pd.read_csv(file_path))
                        pmo_table.pmo_state.set_active_project_plan(pmo_table.validate_columns(
                            pmo_table.pmo_state.get_active_project_plan()))
            # Upload data
            # Add a file uploader to allow users to upload their project plan file
            elif pmo_table.choice_project_plan == "Upload":
                with cols[1]:
                    uploaded_file = st.file_uploader("Upload your project plan.", type=[
                                                        'csv'], key="file_uploader_sidebar")
                    if uploaded_file is not None:
                        pmo_table.pmo_state.set_active_project_plan(pd.read_csv(
                            uploaded_file))
                        pmo_table.pmo_state.set_active_project_plan(pmo_table.validate_columns(
                            pmo_table.pmo_state.get_active_project_plan()))
                        # Save dataframe in the folder
                        timestamp = datetime.now(tz=pytz.timezone(
                            'Europe/Paris')).strftime("plan_%Y-%m-%d-%Hh%M")
                        path_csv = os.path.join(
                            pmo_table.folder_project_plan, f"{timestamp}.csv")
                        path_json = os.path.join(
                            pmo_table.folder_project_plan, f"{timestamp}.json")
                        pmo_table.pmo_state.get_active_project_plan().to_csv(
                            path_csv, index=False)
                        with open(path_json, 'w', encoding='utf-8') as f:
                            json.dump(pmo_table.pmo_state.get_active_project_plan().to_json(
                                orient="records", indent=2), f, ensure_ascii=False, indent=4)
                    else:
                        st.warning('You need to upload a csv file.')
                        pmo_table.pmo_state.set_active_project_plan(pmo_table.df_example)
                        pmo_table.pmo_state.set_active_project_plan(pmo_table.validate_columns(
                            pmo_table.pmo_state.get_active_project_plan()))
                        # Save dataframe in the folder
                        timestamp = datetime.now(tz=pytz.timezone(
                            'Europe/Paris')).strftime("plan_%Y-%m-%d-%Hh%M")
                        path_csv = os.path.join(
                            pmo_table.folder_project_plan, f"{timestamp}.csv")
                        path_json = os.path.join(
                            pmo_table.folder_project_plan, f"{timestamp}.json")
                        pmo_table.pmo_state.get_active_project_plan().to_csv(
                            path_csv, index=False)
                        with open(path_json, 'w', encoding='utf-8') as f:
                            json.dump(pmo_table.pmo_state.get_active_project_plan().to_json(
                                orient="records", indent=2), f, ensure_ascii=False, indent=4)
            else:
                pmo_table.pmo_state.set_active_project_plan(pmo_table.df_example)
                pmo_table.pmo_state.set_active_project_plan(pmo_table.validate_columns(
                            pmo_table.pmo_state.get_active_project_plan()))
                # Save dataframe in the folder
                timestamp = datetime.now(tz=pytz.timezone(
                    'Europe/Paris')).strftime("plan_%Y-%m-%d-%Hh%M")
                path_csv = os.path.join(
                    pmo_table.folder_project_plan, f"{timestamp}.csv")
                path_json = os.path.join(
                    pmo_table.folder_project_plan, f"{timestamp}.json")
                pmo_table.pmo_state.get_active_project_plan().to_csv(
                    path_csv, index=False)
                with open(path_json, 'w', encoding='utf-8') as f:
                    json.dump(pmo_table.pmo_state.get_active_project_plan().to_json(
                        orient="records", indent=2), f, ensure_ascii=False, indent=4)

    pmo_table.original_project_plan_df = pmo_table.pmo_state.get_active_project_plan().copy()

    with st.sidebar:
        st.write("**Filtering**")
        # Filtering
        with st.expander('Filter', icon=":material/filter_alt:", expanded = True):
            selected_regex_filter_project_name = st.text_input(
                label=PMOTable.NAME_COLUMN_PROJECT_NAME, placeholder=PMOTable.NAME_COLUMN_PROJECT_NAME)
            selected_regex_filter_mission_name = st.text_input(
                label=PMOTable.NAME_COLUMN_MISSION_NAME, placeholder=PMOTable.NAME_COLUMN_MISSION_NAME)
            selected_mission_referee: str = st.multiselect(label=PMOTable.NAME_COLUMN_MISSION_REFEREE,
                options=pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_MISSION_REFEREE].unique(
                ), default=None, placeholder=PMOTable.NAME_COLUMN_MISSION_REFEREE)
            selected_regex_filter_team_members = st.text_input(
                label=PMOTable.NAME_COLUMN_TEAM_MEMBERS, placeholder=PMOTable.NAME_COLUMN_TEAM_MEMBERS)
            options = pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_STATUS].unique()
            #We want to remove "☑️ Closed" if it exists to the default options:
            default_options = [opt for opt in options if opt != Status.CLOSED.value]
            selected_status: str = st.multiselect(label=PMOTable.NAME_COLUMN_STATUS, options=options, placeholder=PMOTable.NAME_COLUMN_STATUS, default = default_options)
            selected_priority: str = st.multiselect(label=PMOTable.NAME_COLUMN_PRIORITY, options=pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_PRIORITY].unique(
            ), default=None, placeholder=PMOTable.NAME_COLUMN_PRIORITY)

        # Set edition to False and mark the project plan as inactive if any filter is applied
        if any([selected_regex_filter_project_name, selected_regex_filter_mission_name, selected_mission_referee, selected_regex_filter_team_members, selected_status, selected_priority]):
            pmo_table.edition = False
            active_plan = pmo_table.pmo_state.get_active_project_plan()
            active_plan.Active = False
            pmo_table.pmo_state.set_active_project_plan(active_plan)

        # Initialize the filter condition to True (for all rows)
        filter_condition = pd.Series(
            True, index=pmo_table.pmo_state.get_active_project_plan().index)

        if selected_regex_filter_project_name:
            filter_condition &= pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_PROJECT_NAME].str.contains(
                selected_regex_filter_project_name, case=False)
        if selected_regex_filter_mission_name:
            filter_condition &= pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_MISSION_NAME].str.contains(
                selected_regex_filter_mission_name, case=False)
        if selected_mission_referee:
            filter_condition &= pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_MISSION_REFEREE].isin(
                                                                                                                    selected_mission_referee)
        if selected_regex_filter_team_members:
            filter_condition &= pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_TEAM_MEMBERS].str.contains(
                selected_regex_filter_team_members, case=False)
        if selected_status:
            filter_condition &= pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_STATUS].isin(
                                                                                                            selected_status)
        if selected_priority:
            filter_condition &= pmo_table.pmo_state.get_active_project_plan()[PMOTable.NAME_COLUMN_PRIORITY].isin(
                                                                                                            selected_priority)

        # Apply the combined filter to mark rows as active
        active_plan = pmo_table.pmo_state.get_active_project_plan()
        active_plan.loc[filter_condition,pmo_table.NAME_COLUMN_ACTIVE] = True
        pmo_table.pmo_state.set_active_project_plan(active_plan)
