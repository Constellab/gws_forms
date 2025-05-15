import os
import pandas as pd
import streamlit as st
from datetime import date
from PIL import Image
from gws_core import StringHelper
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority, Event
from gws_forms.dashboard_pmo.pmo_dto import ProjectDTO, MissionDTO, ProjectPlanDTO, MilestoneDTO
from gws_core.streamlit import StreamlitMenuButton, StreamlitRouter, StreamlitMenuButtonItem, StreamlitContainers, StreamlitHelper


def update_milestone(pmo_table: PMOTable, key: str, milestone: MilestoneDTO):
    # Update the milestone status
    milestone.done = st.session_state[key]
    # Update the processed data
    pmo_table.processed_data = pmo_table._process_data()
    # Save changes
    pmo_table.save_data_in_folder()
    # TODO mettre l'observer ici
    """# Apply the observer -> Update tag folder
    if pmo_table.observer:
        check = pmo_table.observer.update(Event(event_type='update_line'))
        if not check:
            raise Exception("Something got wrong, close the app and try again.")"""


@st.dialog("Delete milestone")
def delete_milestone(pmo_table: PMOTable, project_id: str, mission_id: str, milestone: MilestoneDTO):
    st.warning(
        f"Are you sure you want to delete the milestone {milestone.name}? This action cannot be undone.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove milestone from DTOs
        for project in pmo_table.data.data:
            if project.id == project_id:
                # Find the mission that contains the milestone
                for mission in project.missions:
                    if mission.id == mission_id:
                        # Remove the milestone from the mission
                        mission.milestones.remove(milestone)
                        break
        # Update processed data
        pmo_table.processed_data = pmo_table._process_data()
        # Save changes
        pmo_table.save_data_in_folder()
        st.rerun()


def get_fields_milestone(milestone: MilestoneDTO = None):
    """Get milestone fields with optional existing values

    Args:
        existing_values: Whether to use existing values
        milestone: MilestoneDTO object containing existing values
    """
    # Add fields for milestone details
    milestone_name = st.text_input("Insert your milestone name",
                                   value=milestone.name if milestone else "")
    milestone_done = st.checkbox("Is the milestone done?", value=milestone.done if milestone else False)
    return milestone_name, milestone_done


def get_fields_mission(mission: MissionDTO = None):
    """Get mission fields with optional existing values

    Args:
        existing_values: Whether to use existing values
        mission: MissionDTO object containing existing values
    """
    # Add fields for mission details
    mission_name = st.text_input("Insert your mission name",
                                 value=mission.mission_name if mission else "")
    mission_referee = st.text_input("Insert your mission referee",
                                    value=mission.mission_referee if mission else "")
    team_members = st.text_input("Insert your team members (comma separated)",
                                 value=", ".join(mission.team_members) if mission and mission.team_members else "")

    # Handle start date
    start_date = st.date_input(
        "Insert your start date",
        value=mission.start_date if mission and isinstance(mission.start_date, date) else None
    )

    # Handle end date
    end_date = st.date_input(
        "Insert your end date",
        value=mission.end_date if mission and isinstance(mission.end_date, date) else None
    )

    status = st.selectbox(
        "Select status", Status.get_values(),
        index=Status.get_values().index(mission.status) if mission else 0)
    priority = st.selectbox("Select priority", Priority.get_values(),
                            index=Priority.get_values().index(mission.priority) if mission else 0)
    progress = st.number_input("Insert progress (%)", min_value=0.00, max_value=100.00,
                               value=float(mission.progress) if mission else 0.00, step=0.01)
    return mission_name, mission_referee, team_members, start_date, end_date, status, priority, progress


@st.dialog("Add mission")
def add_mission(pmo_table: PMOTable, selected_project: str):
    with st.form(key="mission_form", clear_on_submit=False, enter_to_submit=True):

        # Add fields for mission details
        mission_name, mission_referee, team_members, start_date, end_date, status, priority, progress = get_fields_mission()
        # TODO faire plusieurs champs -> pb qu'on ne peut pas mettre un button dans un st.form
        """# Get current number of team_members
        team_members_values = pmo_table.pmo_state.get_team_members_number()
        st.write("Team members")
        # Create inputs
        for i in range(1, team_members_values + 1):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text_input(label="Team members", placeholder="Enter the name of your metadata",
                              label_visibility="collapsed", key=f"team_members_{i}")
            with col2:
                if i == team_members_values:
                    # Last row: text input + '+' button in a horizontal layout
                    if st.button("\+", type="primary", key="add_value_button"):
                        team_members_values += 1
                        pmo_table.pmo_state.set_team_members_number(team_members_values)
                        st.rerun()"""

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            if not mission_name:
                st.warning("Mission name cannot be empty")
                return
            # Find project by name and check for existing missions
            for project in pmo_table.data.data:
                if project.name == selected_project:
                    existing_missions = [mission.mission_name for mission in project.missions]
                    if mission_name in existing_missions:
                        st.warning("Mission name must be unique. A mission with this name already exists in the selected project.")
                        return
                    break

            # Find project by name
            project = next((p for p in pmo_table.data.data if p.name == selected_project), None)

            # Create new mission using DTO
            new_mission = MissionDTO(
                id=StringHelper.generate_uuid(),
                mission_name=mission_name,
                mission_referee=mission_referee,
                team_members=[member.strip() for member in team_members.split(",")],
                start_date=start_date,
                end_date=end_date,
                status=status,
                priority=priority,
                progress=progress,
                milestones=[]
            )

            # Add mission to project
            project.missions.append(new_mission)

            # Update processed data
            pmo_table.processed_data = pmo_table._process_data()
            # Save changes
            pmo_table.save_data_in_folder()
            # Set success message in session state
            pmo_table.pmo_state.set_show_success_mission_added(True)
            st.rerun()


@st.dialog("Delete project")
def delete_project(pmo_table: PMOTable, project_id: str):
    project_name = ProjectPlanDTO.get_project_name_by_id(pmo_table.data, project_id)
    st.warning(
        f"Are you sure you want to delete the project {project_name}? This action cannot be undone. All missions will be deleted.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove project from DTOs
        pmo_table.data.data = [p for p in pmo_table.data.data if p.id != project_id]
        # Update processed data
        pmo_table.processed_data = pmo_table._process_data()
        # Save changes
        pmo_table.save_data_in_folder()
        # Set success message in session state
        pmo_table.pmo_state.set_show_success_delete_project(True)
        # Set current project to None
        pmo_table.pmo_state.set_current_project(None)
        pmo_table.pmo_state.set_current_mission(None)
        st.rerun()


@st.dialog("Delete mission")
def delete_mission(pmo_table: PMOTable, project_id: str, mission_id: str):
    mission_name = ProjectPlanDTO.get_mission_name_by_id(pmo_table.data, mission_id)
    st.warning(
        f"Are you sure you want to delete the mission {mission_name}? This action cannot be undone.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove mission from DTOs
        for project in pmo_table.data.data:
            if project.id == project_id:
                project.missions = [m for m in project.missions if m.id != mission_id]
                break

        pmo_table.processed_data = pmo_table._process_data()
        # Save changes
        pmo_table.save_data_in_folder()
        # Set success message in session state
        pmo_table.pmo_state.set_show_success_delete_mission(True)
        # Set current mission to None
        pmo_table.pmo_state.set_current_mission(None)
        st.rerun()


@st.dialog("Edit mission")
def edit_mission(pmo_table: PMOTable, project_id: str, selected_mission: str):
    with st.form(key="edit_mission_form", clear_on_submit=False, enter_to_submit=True):
        for project in pmo_table.data.data:
            if project.id == project_id:
                for mission in project.missions:
                    if mission.mission_name == selected_mission:
                        mission_data = mission
                        break
                break
        # Add fields for mission details with existing values
        mission_name, mission_referee, team_members, start_date, end_date, status, priority, progress = get_fields_mission(
            mission=mission_data)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Update the mission data
            mission_data.mission_name = mission_name
            mission_data.mission_referee = mission_referee
            mission_data.team_members = [member.strip() for member in team_members.split(",") if member.strip()]
            mission_data.start_date = start_date
            mission_data.end_date = end_date
            mission_data.status = status
            mission_data.priority = priority
            mission_data.progress = progress

            # Update processed data
            pmo_table.processed_data = pmo_table._process_data()
            # Save changes
            pmo_table.save_data_in_folder()
            st.rerun()


@st.dialog("Edit project")
def edit_project(pmo_table: PMOTable, selected_project: str):
    with st.form(key="edit_project_form", clear_on_submit=False, enter_to_submit=True):
        # Add fields for project details
        project_name = st.text_input("Insert your project name", value=selected_project)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Check if the project name is the same as previously
            # If so, do nothing and return
            if project_name == selected_project:
                return
            # TODO faire des fonctions pour ça
            # Check if the project name is empty
            if not project_name:
                st.warning("Project name cannot be empty")
                return

            # Check for existing project names
            existing_projects = [item[pmo_table.NAME_COLUMN_PROJECT_NAME]
                                 for item in pmo_table.processed_data]
            if project_name in existing_projects:
                st.warning("Project name must be unique. A project with this name already exists.")
                return

            # Update project name
            for project in pmo_table.data.data:
                if project.name == selected_project:
                    project.name = project_name
                    break

            # Update processed data
            pmo_table.processed_data = pmo_table._process_data()
            # Save changes
            pmo_table.save_data_in_folder()
            st.rerun()


@st.dialog("Edit milestone")
def edit_milestone(pmo_table: PMOTable, milestone: MilestoneDTO):
    with st.form(key="edit_milestone_form", clear_on_submit=False, enter_to_submit=True):
        # Add fields for milestone details with existing values
        milestone_name, milestone_done = get_fields_milestone(milestone=milestone)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Update the milestone data
            milestone.name = milestone_name
            milestone.done = milestone_done

            # Update processed data
            pmo_table.processed_data = pmo_table._process_data()
            # Save changes
            pmo_table.save_data_in_folder()
            st.rerun()


@st.dialog("Add milestone")
def add_milestone(pmo_table: PMOTable, project_id: str,  mission_id: str):
    """Open a dialog to add a milestone to the selected mission"""
    with st.form(key="add_milestone_form", clear_on_submit=False, enter_to_submit=True):
        # Add fields for milestone details
        milestone_name, milestone_done = get_fields_milestone()

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Check if the milestone name is empty
            if not milestone_name:
                st.warning("Milestone name cannot be empty")
                return

            # Create new milestone using DTO
            new_milestone = MilestoneDTO(
                id=StringHelper.generate_uuid(),
                name=milestone_name,
                done=milestone_done
            )

            # Find the mission in the project and add the milestone
            for project in pmo_table.data.data:
                if project.id == project_id:
                    for mission_obj in project.missions:
                        if mission_obj.id == mission_id:
                            mission_obj.milestones.append(new_milestone)
                            break
                break

            # Update processed data
            pmo_table.processed_data = pmo_table._process_data()
            # Save changes
            pmo_table.save_data_in_folder()
            st.rerun()


@st.dialog("Create project")
def create_project(pmo_table: PMOTable):
    with st.form(clear_on_submit=False, enter_to_submit=True, key="project_form"):
        name_project = st.text_input("Insert your project name")

        submit_button = st.form_submit_button(
            label="Submit"
        )

        if submit_button:
            # Check if the project name is empty
            if not name_project:
                st.warning("Project name cannot be empty")
                return
            # Check for existing project names
            existing_projects = [item[pmo_table.NAME_COLUMN_PROJECT_NAME]
                                 for item in pmo_table.processed_data]
            if name_project in existing_projects:
                st.warning("Project name must be unique. A project with this name already exists.")
                return

            # Create new project using DTO
            new_project = ProjectDTO(
                id=StringHelper.generate_uuid(),
                name=name_project,
                missions=[]
            )
            # Update the data structure
            pmo_table.data.data.append(new_project)
            # Update the processed data
            pmo_table.processed_data = pmo_table._process_data()
            # Save changes
            pmo_table.save_data_in_folder()
            # Set success message in session state
            pmo_table.pmo_state.set_show_success_project_created(True)
            pmo_table.pmo_state.set_current_project(name_project)
            st.rerun()


def display_project_plan_tab(pmo_table: PMOTable):
    """Display the DataFrame in Streamlit tabs."""
    router = StreamlitRouter.load_from_session()
    # Define the variable pmo_state
    pmo_state = pmo_table.pmo_state

    # TODO faire une fonction dans state pour gérer les messages de succès
    # Display success message
    if pmo_state.get_show_success_project_created():
        st.toast("Project created successfully!", icon="✅")
        pmo_state.set_show_success_project_created(False)

    if pmo_state.get_show_success_delete_project():
        st.toast("Project deleted successfully!", icon="✅")
        pmo_state.set_show_success_delete_project(False)

    if pmo_state.get_show_success_delete_mission():
        st.toast("Mission deleted successfully!", icon="✅")
        pmo_state.set_show_success_delete_mission(False)

    if pmo_state.get_show_success_mission_added():
        st.toast("Mission added successfully!", icon="✅")
        pmo_state.set_show_success_mission_added(False)

    data = pmo_table.processed_data.copy()
    # Create two columns for layout
    left_col, right_col = st.columns([1, 4])

    # Left column - Project list
    with left_col:

        if st.button("New project", use_container_width=True, icon=":material/add:", type="primary"):
            create_project(pmo_table)

        # Get unique project names, ordered alphabetically
        project_names = sorted(list(set(item[pmo_table.NAME_COLUMN_PROJECT_NAME]
                                        for item in data)))

        # Create radio buttons for project selection
        selected_project = st.radio(
            "Select a project",
            options=project_names,
            index=project_names.index(pmo_state.get_current_project()) if pmo_state.get_current_project() else 0,
            label_visibility="collapsed"
        )
        project_id = ProjectPlanDTO.get_project_id_by_name(pmo_table.data, selected_project)

    # Right column - Project details
    with right_col:
        if selected_project:
            pmo_table.pmo_state.set_current_project(selected_project)
            # Create a container for the header with project title and action buttons
            header_col1, header_col2 = st.columns([6, 1])
            with header_col1:
                st.header(f"{selected_project}")
            with header_col2:
                button_menu_project = StreamlitMenuButton(key="button_menu_project")
                add_mission_button = StreamlitMenuButtonItem(label='Add mission', material_icon='add',
                                                             on_click=lambda: add_mission(pmo_table, selected_project))
                button_menu_project.add_button_item(add_mission_button)
                edit_project_button = StreamlitMenuButtonItem(
                    label='Edit project', material_icon='edit',
                    on_click=lambda: edit_project(pmo_table, selected_project))
                button_menu_project.add_button_item(edit_project_button)
                delete_project_button = StreamlitMenuButtonItem(
                    label='Delete project', material_icon='delete', color='warn',
                    on_click=lambda: delete_project(pmo_table, project_id))
                button_menu_project.add_button_item(delete_project_button)

                button_menu_project.render()

            # Filter data for selected project
            project_data = [item for item in data
                            if item[pmo_table.NAME_COLUMN_PROJECT_NAME] == selected_project]
            # If there is no mission set yet, return
            if pmo_table.NAME_COLUMN_MISSION_NAME not in project_data[0]:
                return
            # Define status order mapping
            status_order = Status.get_order()

            # Sort project_data by status first, then mission name
            project_data.sort(key=lambda x: (
                status_order.get(x.get(pmo_table.NAME_COLUMN_STATUS)),  # Status order
                x.get(pmo_table.NAME_COLUMN_MISSION_NAME).lower()  # Mission name alphabetically
            ))

            # Display project information
            for mission in project_data:
                mission_name = mission.get(pmo_table.NAME_COLUMN_MISSION_NAME)
                pmo_table.pmo_state.set_current_mission(mission_name)
                mission_id = mission.get(pmo_table.NAME_MISSION_ID)
                # st.markdown("---")
                with st.expander(mission_name, expanded=True):
                    header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
                    with header_col1:
                        st.subheader(mission_name)
                    with header_col2:
                        # Open note in a hidden page
                        if st.button("View note", icon=":material/visibility:", use_container_width=True,
                                     key=f"view_note_{mission_id}"):
                            router.navigate('notes')
                    with header_col3:
                        button_menu_mission = StreamlitMenuButton(
                            key=f"button_menu_mission_{mission_id}")

                        # Create closure functions to capture the current values
                        def make_edit_callback(pmo_table, p_id, m_name):
                            return lambda: edit_mission(pmo_table, p_id, m_name)

                        def make_delete_callback(pmo_table, p_id, m_id):
                            return lambda: delete_mission(pmo_table, p_id, m_id)

                        edit_mission_button = StreamlitMenuButtonItem(
                            label='Edit mission',
                            material_icon='edit',
                            on_click=make_edit_callback(pmo_table, project_id, mission_name),
                            key=f"edit_mission_{mission_id}")

                        delete_mission_button = StreamlitMenuButtonItem(
                            label='Delete mission',
                            material_icon='delete',
                            color='warn',
                            on_click=make_delete_callback(pmo_table, project_id, mission_id),
                            key=f"delete_mission_{mission_id}")

                        button_menu_mission.add_button_item(edit_mission_button)
                        button_menu_mission.add_button_item(delete_mission_button)
                        button_menu_mission.render()

                    col1, col2, col3 = st.columns(3)

                    # Only display if priority exists
                    priority = mission.get(pmo_table.NAME_COLUMN_PRIORITY)
                    if priority and priority != Priority.NONE.value:
                        with col1:
                            st.write(priority)

                    # Only display if status exists
                    status = mission.get(pmo_table.NAME_COLUMN_STATUS)
                    if status and status != Status.NONE.value:
                        with col2:
                            st.write(status)

                    # Only display if progress exists
                    progress = mission.get(pmo_table.NAME_COLUMN_PROGRESS)
                    if progress is not None:
                        with col3:
                            # Display progress as a percentage
                            st.write(f"{str(progress)}%")

                    # Only display referee if exists
                    referee = mission.get(pmo_table.NAME_COLUMN_MISSION_REFEREE)
                    if referee:
                        st.markdown(f"**{pmo_table.NAME_COLUMN_MISSION_REFEREE}:** {referee}")

                    # Only display dates if they exist
                    start_date = mission.get(pmo_table.NAME_COLUMN_START_DATE)
                    end_date = mission.get(pmo_table.NAME_COLUMN_END_DATE)
                    if start_date or end_date:
                        date_str = f"{start_date if start_date else ''}"
                        date_str += f" - {end_date if end_date else ''}"
                        st.markdown(f"**Date:** {date_str}")

                    # Only display team members if exists
                    team_members = mission.get(pmo_table.NAME_COLUMN_TEAM_MEMBERS)
                    if team_members and team_members != "No members" and team_members != [""]:
                        team_members_str = ", ".join(team_members)
                        st.markdown(f"**{pmo_table.NAME_COLUMN_TEAM_MEMBERS}:** {team_members_str}")

                    # Only display milestones if exists
                    milestones = mission.get(pmo_table.NAME_COLUMN_MILESTONES)

                    title_col, button_col = StreamlitContainers.columns_with_fit_content(
                        key=f"milestone_container_{mission_id}",
                        cols=[1, 'fit-content'])
                    with button_col:
                        st.button("Add milestone", icon=":material/add:",
                                  use_container_width=True,
                                  key=f"add_milestone_{mission_id}",
                                  on_click=add_milestone,
                                  args=(pmo_table, project_id, mission_id,))
                    if milestones:
                        with title_col:
                            st.markdown(f"**{pmo_table.NAME_COLUMN_MILESTONES}:**")
                        i = 0
                        for milestone in milestones:
                            button_key = f"edit_milestone_{i}_{mission_id}"
                            button_css_class = StreamlitHelper.get_element_css_class(button_key)
                            col1, col2 = StreamlitContainers.columns_with_fit_content(
                                f'milestone_{i}_{mission_id}', cols=[1, 'fit-content'],
                                additional_style=f"""
                                                                                    [CLASS_NAME] .{button_css_class} {{
                                                                                        opacity: 0;
                                                                                    }}

                                                                                    [CLASS_NAME]:hover .{button_css_class} {{
                                                                                        opacity: 1;
                                                                                    }}
                                                                                    """)

                            name = milestone.name
                            done = milestone.done

                            with col1:

                                # Format the milestone display
                                task_label = f"~~{name.strip()}~~" if done else name
                                key = f"{name}_{mission.get(pmo_table.NAME_PROJECT_ID)}_{mission.get(pmo_table.NAME_MISSION_ID)}_{i}"

                                st.checkbox(
                                    label=task_label,
                                    key=key,
                                    value=done,
                                    on_change=update_milestone,
                                    args=(pmo_table, key, milestone,))

                            with col2:
                                button_menu_milestone = StreamlitMenuButton(key=button_key)
                                edit_milestone_button = StreamlitMenuButtonItem(
                                    label='Edit milestone', material_icon='edit',
                                    on_click=lambda: edit_milestone(pmo_table, milestone))
                                button_menu_milestone.add_button_item(edit_milestone_button)
                                delete_milestone_button = StreamlitMenuButtonItem(
                                    label='Delete milestone', material_icon='delete', color='warn',
                                    on_click=lambda: delete_milestone(pmo_table, project_id, mission_id, milestone))
                                button_menu_milestone.add_button_item(delete_milestone_button)

                                button_menu_milestone.render()

                            i += 1

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

    # TODO apply the observer somewhere
    """# Apply the observer -> Update tag folder
    if pmo_table.observer:
        check = pmo_table.observer.update(Event(event_type='update_line'))
        if not check:
            raise Exception("Something got wrong, close the app and try again.")"""
