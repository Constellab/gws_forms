import os
import json
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO


def display_settings_tab(pmo_table: PMOTable):

    st.write("**Project Plan Files**")
    # List all JSON files in the saved directory
    files = sorted([f.split(".json")[0] for f in os.listdir(
        pmo_table.folder_project_plan) if f.endswith(".json")], reverse=True)

    cols = st.columns(2)
    options = ["Load", "Upload"] if files else ["Upload"]
    with cols[0]:
        choice_project_plan = st.selectbox("Select an option", options, key="choice_project_plan")

    # Load data
    if choice_project_plan == "Load":
        with cols[1]:
            # Show a selectbox to choose one file; by default, choose the last one
            selected_file = st.selectbox(
                label="Choose an existing project plan", options=files, index=0,
                placeholder="Select a project plan", key="selected_file_settings")
            # Load the selected file and display its contents
            if selected_file:
                pmo_table = PMOTable(folder_project_plan=pmo_table.folder_project_plan,
                                     folder_details=pmo_table.folder_details,
                                     folder_change_log=pmo_table.folder_change_log, selected_file=selected_file)
                # Set current project to None
                pmo_table.pmo_state.set_current_project(None)
                pmo_table.pmo_state.set_current_mission(None)

    # Upload data
    # Add a file uploader to allow users to upload their project plan file
    elif choice_project_plan == "Upload":
        with cols[1]:
            uploaded_file = st.file_uploader("Upload your project plan.", type=[
                'json'], key="file_uploader_sidebar")
            if uploaded_file is not None:
                loaded_data = json.loads(uploaded_file.getvalue().decode('utf-8'))
                pmo_table.data = ProjectPlanDTO.from_json(loaded_data)
                pmo_table.commit_and_save()
                # Set current project to None
                pmo_table.pmo_state.set_current_project(None)
                pmo_table.pmo_state.set_current_mission(None)
            else:
                st.warning('You need to upload a JSON file.')
                # Use example data - already in the pmo_table
                # Save data in the folder
                pmo_table = PMOTable(folder_project_plan=pmo_table.folder_project_plan,
                                     folder_details=pmo_table.folder_details,
                                     folder_change_log=pmo_table.folder_change_log)
                pmo_table.save_data_in_folder()
                # Set current project to None
                pmo_table.pmo_state.set_current_project(None)
                pmo_table.pmo_state.set_current_mission(None)

        # Load and allow users to download the JSON template
        template_path = os.path.join(os.path.abspath(
            os.path.dirname(__file__)), "template.json")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_json = f.read()

        st.download_button(
            label="Download template",
            icon=":material/help_outline:",
            data=template_json,
            file_name='project_template.json',
            mime='application/json',
        )

    # st.write("**Language**")
    # TODO faire le choix de la langue
