from datetime import date, datetime
import streamlit as st
from gws_core import StringHelper
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority
from gws_forms.dashboard_pmo.pmo_dto import ProjectDTO, MissionDTO, ProjectPlanDTO, MilestoneDTO


def check_project_name_unique_and_not_empty(project_name: str, pmo_table: PMOTable) -> None:
    # Check if the project name is empty
    if not project_name:
        st.warning("Project name cannot be empty")
        return True

    # Check for existing project names
    existing_projects = [project.name for project in pmo_table.data.data]
    if project_name in existing_projects:
        st.warning("Project name must be unique. A project with this name already exists.")
        return True

    return False


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
                               value=float(mission.progress) if mission else 0.00, step=0.01, format="%0.2f")
    return mission_name, mission_referee, team_members, start_date, end_date, status, priority, progress


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

        pmo_table.commit_and_save()
        st.rerun()


@st.dialog("Add mission")
def add_mission(pmo_table: PMOTable, current_project: ProjectDTO):
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
                if project.name == current_project.name:
                    existing_missions = [mission.mission_name for mission in project.missions]
                    if mission_name in existing_missions:
                        st.warning("Mission name must be unique. A mission with this name already exists in the selected project.")
                        return
                    break

            # Create new mission using DTO
            mission_id = StringHelper.generate_uuid()
            new_mission = MissionDTO(
                id=mission_id,
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
            current_project.missions.append(new_mission)

            # Track status change when adding new mission
            new_entry = {
                "mission_id": mission_id,
                "project": current_project.name,
                "mission": mission_name,
                "status_before": None,  # No previous status for new mission
                "status_after": status,
                "date": datetime.now().isoformat()
            }
            pmo_table.pmo_state.append_status_change_log(new_entry)
            # Convert the log to JSON
            pmo_table.pmo_state.convert_log_to_json()

            pmo_table.commit_and_save()
            # Set success message in session state
            pmo_table.pmo_state.set_show_success_mission_added(True)
            st.rerun()


@st.dialog("Delete project")
def delete_project(pmo_table: PMOTable, current_project: ProjectDTO):
    st.warning(
        f"Are you sure you want to delete the project {current_project.name}? This action cannot be undone. All missions will be deleted.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove project from DTOs
        pmo_table.data.data = [p for p in pmo_table.data.data if p.id != current_project.id]
        # Save
        pmo_table.commit_and_save()
        # Set success message in session state
        pmo_table.pmo_state.set_show_success_delete_project(True)
        # Set current project to None
        pmo_table.pmo_state.set_current_project(None)
        pmo_table.pmo_state.set_current_mission(None)
        st.rerun()


@st.dialog("Delete mission")
def delete_mission(pmo_table: PMOTable, project_id: str, mission_id: str):
    mission_name = ProjectPlanDTO.get_mission_by_id(pmo_table.data, mission_id).mission_name
    st.warning(
        f"Are you sure you want to delete the mission {mission_name}? This action cannot be undone.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove mission from DTOs
        for project in pmo_table.data.data:
            if project.id == project_id:
                project.missions = [m for m in project.missions if m.id != mission_id]
                break

        pmo_table.commit_and_save()
        # Set success message in session state
        pmo_table.pmo_state.set_show_success_delete_mission(True)
        # Set current mission to None
        pmo_table.pmo_state.set_current_mission(None)
        st.rerun()


@st.dialog("Edit mission")
def edit_mission(pmo_table: PMOTable, current_project: ProjectDTO, current_mission: MissionDTO):
    with st.form(key="edit_mission_form", clear_on_submit=False, enter_to_submit=True):

        # Store original status before changes
        original_status = current_mission.status

        # Add fields for mission details with existing values
        mission_name, mission_referee, team_members, start_date, end_date, status, priority, progress = get_fields_mission(
            mission=current_mission)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Check if status has changed
            if status != original_status:
                # Track status change
                new_entry = {
                    "mission_id": current_mission.id,
                    "project": current_project.name,
                    "mission": mission_name,
                    "status_before": original_status,
                    "status_after": status,
                    "date": datetime.now().isoformat()
                }
                pmo_table.pmo_state.append_status_change_log(new_entry)
                # Convert the log to JSON
                pmo_table.pmo_state.convert_log_to_json()

            # Update the mission data
            current_mission.mission_name = mission_name
            current_mission.mission_referee = mission_referee
            current_mission.team_members = [member.strip() for member in team_members.split(",") if member.strip()]
            current_mission.start_date = start_date
            current_mission.end_date = end_date
            current_mission.status = status
            current_mission.priority = priority
            current_mission.progress = progress

            pmo_table.commit_and_save()
            st.rerun()


@st.dialog("Edit project")
def edit_project(pmo_table: PMOTable, current_project: ProjectDTO):

    with st.form(key="edit_project_form", clear_on_submit=False, enter_to_submit=True):
        existing_project_name = current_project.name
        # Add fields for project details
        project_name = st.text_input("Insert your project name", value=existing_project_name)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Check if the project name is the same as previously
            # If so, do nothing and return
            if project_name == existing_project_name:
                return
            if check_project_name_unique_and_not_empty(project_name, pmo_table):
                return

            # Update project name
            pmo_table.update_project_name_by_id(current_project.id, project_name)

            pmo_table.commit_and_save()
            st.rerun()


@st.dialog("Edit milestone")
def edit_milestone(pmo_table: PMOTable, milestone_id: str):
    milestone = ProjectPlanDTO.get_milestone_by_id(pmo_table.data, milestone_id)
    with st.form(key="edit_milestone_form", clear_on_submit=False, enter_to_submit=True):
        # Add fields for milestone details with existing values
        milestone_name, milestone_done = get_fields_milestone(milestone=milestone)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Update the milestone data
            milestone.name = milestone_name
            milestone.done = milestone_done

            pmo_table.commit_and_save()
            st.rerun()


@st.dialog("Add milestone")
def add_milestone(pmo_table: PMOTable, project_id: str, mission_id: str):
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

            # Find the project and mission to add the milestone
            project = next((p for p in pmo_table.data.data if p.id == project_id), None)
            if project:
                mission = next((m for m in project.missions if m.id == mission_id), None)
                if mission:
                    mission.milestones.append(new_milestone)
            pmo_table.commit_and_save()
            st.rerun()


@st.dialog("Create project")
def create_project(pmo_table: PMOTable):
    with st.form(clear_on_submit=False, enter_to_submit=True, key="project_form"):
        name_project = st.text_input("Insert your project name")

        submit_button = st.form_submit_button(
            label="Submit"
        )

        if submit_button:
            if check_project_name_unique_and_not_empty(name_project, pmo_table):
                return

            # Create new project using DTO
            new_project = ProjectDTO(
                id=StringHelper.generate_uuid(),
                name=name_project,
                missions=[],
                folder_root_id="",
                folder_project_id=""
            )
            # Update the data structure
            pmo_table.data.data.append(new_project)
            # Save
            pmo_table.commit_and_save()
            # Set success message in session state
            pmo_table.pmo_state.set_show_success_project_created(True)
            pmo_table.pmo_state.set_current_project(new_project)
            st.rerun()
