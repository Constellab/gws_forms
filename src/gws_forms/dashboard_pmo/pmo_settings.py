import os
import json
from typing import List
import streamlit as st
import numpy as np
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO, MissionDTO, MilestoneDTO, UserDTO
from gws_core import User, UserGroup, StringHelper
from gws_core.streamlit import StreamlitContainers


def missions_change(pmo_table : PMOTable, number_predefined_missions : int):
    list_predefined_missions : List[MissionDTO]= []
    for i in range(0, number_predefined_missions + 1):
        mission_name = st.session_state.get(f"predefined_missions_{i}", "")
        milestones_str = st.session_state.get(f"predefined_milestones_{i}", "")
        if mission_name != "" or milestones_str != "":
            milestone_names = [m.strip() for m in milestones_str.split(",") if m.strip()]
            milestones = [
                MilestoneDTO(id=StringHelper.generate_uuid(), name=name, done=False)
                for name in milestone_names
            ]
            mission = MissionDTO(
                mission_name=mission_name,
                mission_referee="",
                team_members=[],
                start_date=None,
                end_date=None,
                milestones=milestones,
                status=Status.IN_PROGRESS.value if i == 0 else Status.NONE.value,
                priority=Priority.NONE.value,
                progress=0.0,
                id=StringHelper.generate_uuid()
            )
            list_predefined_missions.append(mission)
    pmo_table.set_predefined_missions(list_predefined_missions)

    if pmo_table.missions_order == []:
        if pmo_table.pmo_state.get_predefined_missions():
            for mission in pmo_table.pmo_state.get_predefined_missions():
                pmo_table.missions_order.append(mission.mission_name)
            pmo_table.missions_order = pmo_table.pmo_state.get_predefined_missions()


def display_settings_tab(pmo_table: PMOTable):
    pmo_state = pmo_table.pmo_state

    with st.expander("**Project Plan Files**", expanded=False):
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
                                        folder_change_log=pmo_table.folder_change_log, folder_settings= pmo_table.folder_settings, selected_file=selected_file)
                    # Set current project to None
                    pmo_state.set_current_project(None)
                    pmo_state.set_current_mission(None)

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
                    pmo_state.set_current_project(None)
                    pmo_state.set_current_mission(None)
                else:
                    st.warning('You need to upload a JSON file.')
                    # Use example data - already in the pmo_table
                    # Save data in the folder
                    pmo_table = PMOTable(folder_project_plan=pmo_table.folder_project_plan,
                                        folder_details=pmo_table.folder_details,
                                        folder_change_log=pmo_table.folder_change_log, folder_settings= pmo_table.folder_settings)
                    pmo_table.save_data_in_folder()
                    # Set current project to None
                    pmo_state.set_current_project(None)
                    pmo_state.set_current_mission(None)

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

    with st.expander("**Folders**", expanded=False):
        if pmo_table.pmo_state.is_standalone():
            st.info("These features aren't available in demo mode. Try them out in a lab on Constellab!")
        col1, col2 = st.columns(2)
        with col1:
            def on_checkbox_change():
                pmo_table.set_create_folders_in_space(st.session_state["create_folders_in_space"])
            st.checkbox(
                "Create folders in space",
                key="create_folders_in_space",
                disabled=True if pmo_table.pmo_state.is_standalone() else False,
                on_change=on_checkbox_change
            )
        with col2:
            def on_text_input_share_change():
                pmo_table.set_share_folders_with_team(st.session_state["share_folders_with_team"])
            st.text_input(
                "Share folders with a team",
                key="share_folders_with_team",
                help="Enter the id of the team to share folders with.",
                disabled=True if pmo_table.pmo_state.is_standalone() else False,
                on_change=on_text_input_share_change
            )

    with st.expander("**Company members**", expanded=False):
        def on_multiselect_change():
            pmo_table.set_company_members(st.session_state["company_members"])
        list_lab_users = pmo_state.get_list_lab_users()
        list_names = [user.first_name for user in list_lab_users]

        # Convert company members to strings before combining
        company_member_names = [member if isinstance(member, str) else member.first_name for member in pmo_table.get_company_members()]
        options = list(np.unique(list_names + company_member_names))

        st.multiselect(
            "Select company members",
            options=options,
            key="company_members",
            on_change=on_multiselect_change
        )

    with st.expander("**Predefined missions**", expanded=False):

        # Get current number of missions
        number_predefined_missions = len(pmo_state.get_predefined_missions())
        # Create inputs
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Missions**")
        with col2:
            st.write("**Milestones**")
        for i in range(0, number_predefined_missions + 1):
            # Get current mission name and milestones as comma-separated string
            current_mission = pmo_state.get_predefined_missions()[i] if i < number_predefined_missions else None
            mission_name_value = current_mission.mission_name if current_mission else ""
            milestones_value = (
                ", ".join([m.name for m in current_mission.milestones]) if current_mission else ""
            )
            col1, col2 = StreamlitContainers.columns_with_fit_content(
                    key=f"container_{i}",
                    cols=[1, 1], vertical_align_items='start')

            with col1:
                st.text_input(
                    label="Predefined missions",
                    value=mission_name_value,
                    placeholder="Enter the name of your mission",
                    label_visibility="collapsed",
                    key=f"predefined_missions_{i}",
                    on_change=missions_change,
                    args = (pmo_table, number_predefined_missions,)
                )
            with col2:
                st.text_area(
                    label="Predefined milestones (comma-separated)",
                    value=milestones_value,
                    placeholder="Enter the name of your milestones (comma-separated)",
                    label_visibility="collapsed",
                    key=f"predefined_milestones_{i}",
                    on_change=missions_change,
                    args = (pmo_table, number_predefined_missions,)
                )

        # Check for duplicate mission names
        mission_names = [m.mission_name.strip() for m in pmo_state.get_predefined_missions() if m.mission_name.strip()]
        duplicates = set([name for name in mission_names if mission_names.count(name) > 1])
        if duplicates:
            st.warning(f"Duplicate mission names found: {', '.join(duplicates)}. Each predefined mission name must be unique.")
