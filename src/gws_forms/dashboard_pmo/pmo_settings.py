import os
import json
import streamlit as st
import pandas as pd
from PIL import Image
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO


def display_settings_tab(pmo_table: PMOTable):

    st.write("**Project Plan Files**")
    # List all JSON files in the saved directory
    files = sorted([f.split(".json")[0] for f in os.listdir(
        pmo_table.folder_project_plan) if f.endswith(".json")], reverse=True)

    cols = st.columns(2)
    options = ["Load", "Upload", "Fill manually"] if files else ["Upload", "Fill manually"]
    with cols[0]:
        pmo_table.choice_project_plan = st.selectbox("Select an option", options, key="choice_project_plan")

    # Load data
    if pmo_table.choice_project_plan == "Load":
        with cols[1]:
            # Show a selectbox to choose one file; by default, choose the last one
            selected_file = st.selectbox(
                label="Choose an existing project plan", options=files, index=0,
                placeholder="Select a project plan", key="selected_file_settings")
            # Load the selected file and display its contents
            if selected_file:
                selected_file = selected_file + ".json"
                file_path = os.path.join(
                    pmo_table.folder_project_plan, selected_file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    pmo_table.data = ProjectPlanDTO.from_json(loaded_data)
                    pmo_table.processed_data = pmo_table._process_data()
                    pmo_table.save_data_in_folder()
                    pmo_table.pmo_state.set_current_pmo_table(pmo_table)
                    # Set current project to None
                    pmo_table.pmo_state.set_current_project(None)
                    pmo_table.pmo_state.set_current_mission(None)

    # Upload data
    # Add a file uploader to allow users to upload their project plan file
    elif pmo_table.choice_project_plan == "Upload":
        with cols[1]:
            uploaded_file = st.file_uploader("Upload your project plan.", type=[
                'json'], key="file_uploader_sidebar")
            if uploaded_file is not None:
                loaded_data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                pmo_table.data = ProjectPlanDTO.from_json(loaded_data)
                pmo_table.processed_data = pmo_table._process_data()
                # pmo_table.validate_columns()
                # Save data in the folder
                pmo_table.save_data_in_folder()
                pmo_table.pmo_state.set_current_pmo_table(pmo_table)
                # Set current project to None
                pmo_table.pmo_state.set_current_project(None)
                pmo_table.pmo_state.set_current_mission(None)
            else:
                st.warning('You need to upload a JSON file.')
                # Use example data - already in the pmo_table
                # pmo_table.validate_columns()
                # Save data in the folder
                pmo_table = PMOTable(json_path=None, folder_project_plan=pmo_table.folder_project_plan,
                                     folder_details=pmo_table.folder_details, folder_change_log=pmo_table.folder_change_log)
                pmo_table.save_data_in_folder()
                pmo_table.pmo_state.set_current_pmo_table(pmo_table)
                # Set current project to None
                pmo_table.pmo_state.set_current_project(None)
                pmo_table.pmo_state.set_current_mission(None)
    else:
        # Use example data - already in the pmo_table
        # pmo_table.validate_columns()
        # Save data in the folder
        pmo_table = PMOTable(json_path=None, folder_project_plan=pmo_table.folder_project_plan,
                             folder_details=pmo_table.folder_details, folder_change_log=pmo_table.folder_change_log)
        pmo_table.save_data_in_folder()
        pmo_table.pmo_state.set_current_pmo_table(pmo_table)
        # Set current project to None
        pmo_table.pmo_state.set_current_project(None)
        pmo_table.pmo_state.set_current_mission(None)

    if pmo_table.choice_project_plan != "Load":
        # Add a template screenshot as an example
        with st.expander('Download the project plan template', icon=":material/help_outline:"):

            # Allow users to download the template
            @st.cache_data
            def convert_df(df: pd.DataFrame) -> pd.DataFrame:
                return df.to_csv().encode('utf-8')
            df_template = pd.read_csv(os.path.join(os.path.abspath(
                os.path.dirname(__file__)), "template.csv"), index_col=False)

            csv = convert_df(df_template)
            st.download_button(
                label="Download Template",
                data=csv,
                file_name='project_template.csv',
                mime='text/csv',
            )

            image = Image.open(os.path.join(os.path.abspath(os.path.dirname(
                __file__)), "example_template_pmo.png"))  # template screenshot provided as an example
            st.image(
                image,  caption='Make sure you use the same column names as in the template')

    st.write("**Language**")
    # TODO faire le choix de la langue
