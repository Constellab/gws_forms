import os
import json
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO


def display_sidebar(pmo_table: PMOTable):
    with st.sidebar:
        st.write("**Load files**")
        with st.expander('Project plan file', icon=":material/description:"):
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
                        placeholder="Select a project plan", key="selected_file_sidebar")
                    # Load the selected file and display its contents
                    if selected_file:
                        selected_file = selected_file + ".json"
                        file_path = os.path.join(
                            pmo_table.folder_project_plan, selected_file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            loaded_data = json.load(f)
                            pmo_table.data = ProjectPlanDTO.from_json(loaded_data)
                            pmo_table.processed_data = pmo_table._process_data()
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
                    else:
                        st.warning('You need to upload a JSON file.')
                        # Use example data - already in the pmo_table
                        # pmo_table.validate_columns()
                        # Save data in the folder
                        pmo_table.save_data_in_folder()
            else:
                # Use example data - already in the pmo_table
                # pmo_table.validate_columns()
                # Save data in the folder
                pmo_table.save_data_in_folder()
