from datetime import date, datetime

import numpy as np
import streamlit as st
from gws_core import (CurrentUserService, ExternalSpaceCreateFolder,
                      SpaceRootFolderUserRole, SpaceService, StringHelper, Tag)
from gws_core.streamlit import StreamlitAuthenticateUser

from gws_forms.dashboard_pmo.pmo_dto import (ClientDTO, MilestoneDTO,
                                             MissionDTO, ProjectDTO,
                                             ProjectPlanDTO)
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Priority, Status


def check_set_client_and_project_name_unique_and_not_empty(
        client_name: str, project_name: str, pmo_table: PMOTable) -> None:

    # Check if the project name is empty
    if not project_name:
        st.warning("Project name cannot be empty")
        return True

    for client in pmo_table.data.data:
        if client.client_name == client_name:
            # Check if the project name is already used for this client
            for project in client.projects:
                if project.name == project_name:
                    st.warning("A project with this name already exists for this client.")
                    return True
    return False


def check_client_name_unique_and_not_empty(client_name: str, pmo_table: PMOTable) -> None:
    # Check if the client name is empty
    if not client_name:
        st.warning("Client name cannot be empty")
        return True

    for client in pmo_table.data.data:
        if client.client_name == client_name:
            st.warning("A client with this name already exists.")
            return True
    return False


def update_milestones_in_global_follow_up_mission(
        pmo_table: PMOTable, current_project: ProjectDTO, mission: MissionDTO):
    if current_project.global_follow_up_mission_id != "":
        # If the project has a Global Follow-up mission, we update its milestones
        # to include the new mission
        global_follow_up_mission = ProjectPlanDTO.get_mission_by_id(
            pmo_table.data, current_project.global_follow_up_mission_id)
        if global_follow_up_mission:
            # Create a new milestone for the Global Follow-up mission
            new_milestone = MilestoneDTO(
                id=StringHelper.generate_uuid(),
                name=mission.mission_name,
                done=False
            )
            global_follow_up_mission.milestones.append(new_milestone)


def log_new_mission_status(pmo_table: PMOTable, project: ProjectDTO, mission: MissionDTO):
    # Track status change when adding new mission
    new_entry = {
        "mission_id": mission.id,
        "project": project.name,
        "mission": mission.mission_name,
        "status_before": None,  # No previous status for new mission
        "status_after": mission.status,
        "date": datetime.now().isoformat()
    }
    pmo_table.pmo_state.append_status_change_log(new_entry)


def create_root_folder_in_space(pmo_table: PMOTable, current_client: ClientDTO):
    with StreamlitAuthenticateUser():
        # Create folder in the space
        space_service = SpaceService.get_instance()
        # We create a root folder in the space
        # We parse value to ensure it is a valid tag format because auto parse is not longer availaible
        # for values in lab
        current_client_name = current_client.client_name
        current_client_name = Tag.parse_tag(current_client_name)

        folder_root_client = ExternalSpaceCreateFolder(
            name=current_client.client_name,
            tags=[Tag(key="type", value="client", auto_parse=True),
                  Tag(key="client", value=current_client_name, auto_parse=True)])
        folder_root_client_space = space_service.create_root_folder(folder=folder_root_client)
        # Share
        id_team_to_share = pmo_table.pmo_state.get_share_folders_with_team()
        if not id_team_to_share:
            # Get the id of the current user to share the folder with
            id_team_to_share = CurrentUserService.get_current_user().id
        space_service.share_root_folder(root_folder_id=folder_root_client_space.id,
                                        group_id=id_team_to_share, role=SpaceRootFolderUserRole.OWNER)
        space_service.share_root_folder_with_current_lab(root_folder_id=folder_root_client_space.id)
        current_client.folder_root_id = folder_root_client_space.id


def create_subfolders_in_space(pmo_table: PMOTable, current_client: ClientDTO, current_project: ProjectDTO):
    with StreamlitAuthenticateUser():
        space_service = SpaceService.get_instance()

        # Retrieve the id of the folder root client already created
        folder_root_client_space_id = current_client.folder_root_id
        if folder_root_client_space_id == "":
            # If the root folder does not exist, we create it
            create_root_folder_in_space(pmo_table, current_client)

            # Retrieve the id of the folder root client after creation
            folder_root_client_space_id = current_client.folder_root_id

        # Create the subfolders
        folder_project = ExternalSpaceCreateFolder(
            name=current_project.name)
        folder_project_space = space_service.create_child_folder(
            parent_id=folder_root_client_space_id, folder=folder_project)
        current_project.folder_project_id = folder_project_space.id


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


def get_fields_mission(pmo_table: PMOTable, mission: MissionDTO = None):
    """Get mission fields with optional existing values

    Args:
        existing_values: Whether to use existing values
        mission: MissionDTO object containing existing values
    """
    # Add fields for mission details
    mission_name = st.text_input("Insert your mission name",
                                 value=mission.mission_name if mission else "")
    if mission and mission.mission_referee != "":
        options_mission_referee = np.unique(pmo_table.pmo_state.get_company_members() + [mission.mission_referee])
        # Convert to list for the index method
        options_mission_referee_list = options_mission_referee.tolist()
        index = options_mission_referee_list.index(
            mission.mission_referee) if mission.mission_referee in options_mission_referee_list else 0
    else:
        options_mission_referee = pmo_table.pmo_state.get_company_members()
        index = None
    mission_referee = st.selectbox("Select your mission referee",
                                   options=options_mission_referee,
                                   index=index)
    if mission and mission.team_members:
        # If the mission already has team members, we add them to the options
        options_team_members = np.unique(pmo_table.pmo_state.get_company_members() + mission.team_members)
    else:
        options_team_members = np.unique(pmo_table.pmo_state.get_company_members())
    team_members = st.multiselect("Select your team members",
                                  options=options_team_members,
                                  default=mission.team_members if mission and mission.team_members else [])

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
        for client in pmo_table.data.data:
            for project in client.projects:
                if project.id == project_id:
                    # Find the mission that contains the milestone
                    for mission in project.missions:
                        if mission.id == mission_id:
                            # Remove the milestone from the mission
                            mission.milestones.remove(milestone)
                            break

        pmo_table.commit_and_save()
        st.rerun()


@st.dialog("Add predefined missions")
def add_predefined_missions(pmo_table: PMOTable, current_project: ProjectDTO):
    predefined_missions_dict = pmo_table.pmo_state.get_predefined_missions()
    if not predefined_missions_dict:
        st.warning("No predefined missions available. Please add some in the settings.")
        return

    st.warning(
        f"Are you sure to add the predefined missions defined in the settings ? ")
    if st.button("Add", use_container_width=True, icon=":material/add:"):
        # Add missions to the project
        first_mission = None
        for mission_data in predefined_missions_dict:
            if any(mission.mission_name == mission_data.mission_name for mission in current_project.missions):
                continue
            milestones = [
                MilestoneDTO(id=StringHelper.generate_uuid(), name=milestone.name, done=False)
                for milestone in mission_data.milestones if milestone
            ]

            mission_id = StringHelper.generate_uuid()
            new_mission = MissionDTO(
                id=mission_id,
                mission_name=mission_data.mission_name,
                mission_referee=mission_data.mission_referee,
                team_members=mission_data.team_members,
                start_date=datetime.now().strftime("%Y-%m-%d")
                if mission_data.status == Status.IN_PROGRESS.value else None,
                end_date=None,
                milestones=milestones,
                status=mission_data.status,
                priority=Priority.NONE.value, progress=0.0)
            current_project.missions.append(new_mission)

            update_milestones_in_global_follow_up_mission(pmo_table, current_project, new_mission)

            if not first_mission:
                # Keep track of the first mission added
                first_mission = new_mission

            log_new_mission_status(pmo_table, current_project, new_mission)

        # Convert the log to JSON
        pmo_table.pmo_state.convert_log_to_json()

        # Save changes
        pmo_table.commit_and_save()

        # Set success message in session state
        pmo_table.pmo_state.set_show_success_mission_added(True)
        pmo_table.pmo_state.set_current_mission(first_mission)
        # We delete the tree-menu state to remove data concerning the tree
        # So at the next rerun, the tree will be rebuilt and we can set default values
        pmo_table.pmo_state.reset_tree_pmo()
        st.rerun()


@st.dialog("Add mission")
def add_mission(pmo_table: PMOTable, current_project: ProjectDTO):
    with st.form(key="mission_form", clear_on_submit=False, enter_to_submit=True):

        # Add fields for mission details
        mission_name, mission_referee, team_members, start_date, end_date, status, priority, progress = get_fields_mission(
            pmo_table)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            if not mission_name:
                st.warning("Mission name cannot be empty")
                return
            # Find project by name and check for existing missions
            for client in pmo_table.data.data:
                for project in client.projects:
                    if project.name == current_project.name:
                        existing_missions = [mission.mission_name for mission in project.missions]
                        if mission_name in existing_missions:
                            st.warning(
                                "Mission name must be unique. A mission with this name already exists in the selected project.")
                            return
                        break

            # Create new mission using DTO
            mission_id = StringHelper.generate_uuid()
            new_mission = MissionDTO(
                id=mission_id,
                mission_name=mission_name,
                mission_referee=mission_referee if mission_referee else "",
                team_members=team_members,
                start_date=start_date,
                end_date=end_date,
                status=status,
                priority=priority,
                progress=progress,
                milestones=[]
            )

            # Add mission to project
            current_project.missions.append(new_mission)

            update_milestones_in_global_follow_up_mission(pmo_table, current_project, new_mission)

            log_new_mission_status(pmo_table, current_project, new_mission)

            # Convert the log to JSON
            pmo_table.pmo_state.convert_log_to_json()

            pmo_table.commit_and_save()
            # Set success message in session state
            pmo_table.pmo_state.set_show_success_mission_added(True)
            pmo_table.pmo_state.set_current_mission(new_mission)
            # We delete the tree-menu state to remove data concerning the tree
            # So at the next rerun, the tree will be rebuilt and we can set default values
            pmo_table.pmo_state.reset_tree_pmo()
            st.rerun()


@st.dialog("Delete project")
def delete_project(pmo_table: PMOTable, current_project: ProjectDTO):
    st.warning(
        f"Are you sure you want to delete the project {current_project.name}? This action cannot be undone. All missions will be deleted.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove project from DTOs
        for client in pmo_table.data.data:
            client.projects = [p for p in client.projects if p.id != current_project.id]
        # Save
        pmo_table.commit_and_save()
        # Set success message in session state
        pmo_table.pmo_state.set_show_success_delete_project(True)
        # Set current project to None
        pmo_table.pmo_state.set_current_project(None)
        pmo_table.pmo_state.set_current_mission(None)
        # We delete the tree-menu state to remove data concerning the tree
        # So at the next rerun, the tree will be rebuilt and we can set default values
        pmo_table.pmo_state.reset_tree_pmo()
        st.rerun()


@st.dialog("Delete client")
def delete_client(pmo_table: PMOTable, current_client: ClientDTO):
    st.warning(
        f"Are you sure you want to delete the client {current_client.client_name}? This action cannot be undone. All projects and missions will be deleted.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove client from DTOs
        pmo_table.data.data = [c for c in pmo_table.data.data if c.id != current_client.id]
        # Save
        pmo_table.commit_and_save()
        # Set success message in session state
        pmo_table.pmo_state.set_show_success_client_deleted(True)
        # Set current project to None
        pmo_table.pmo_state.set_current_client(None)
        pmo_table.pmo_state.set_current_project(None)
        pmo_table.pmo_state.set_current_mission(None)
        # We delete the tree-menu state to remove data concerning the tree
        # So at the next rerun, the tree will be rebuilt and we can set default values
        pmo_table.pmo_state.reset_tree_pmo()
        st.rerun()


@st.dialog("Delete mission")
def delete_mission(pmo_table: PMOTable, project_id: str, mission_id: str):
    project = ProjectPlanDTO.get_project_by_id(pmo_table.data, project_id)
    if mission_id == project.global_follow_up_mission_id:
        st.warning(
            "You cannot delete the Global Follow-up mission. This mission is used to track the global follow-up of the project.")
        return
    mission_name = ProjectPlanDTO.get_mission_by_id(pmo_table.data, mission_id).mission_name
    st.warning(
        f"Are you sure you want to delete the mission {mission_name}? This action cannot be undone.")
    if st.button("Delete", use_container_width=True, icon=":material/delete:"):
        # Remove mission from DTOs
        for client in pmo_table.data.data:
            for project in client.projects:
                if project.id == project_id:
                    project.missions = [m for m in project.missions if m.id != mission_id]
                    break

        pmo_table.commit_and_save()
        # Set success message in session state
        pmo_table.pmo_state.set_show_success_delete_mission(True)
        # Set current mission to None
        pmo_table.pmo_state.set_current_mission(None)
        # We delete the tree-menu state to remove data concerning the tree
        # So at the next rerun, the tree will be rebuilt and we can set default values
        pmo_table.pmo_state.reset_tree_pmo()
        st.rerun()


@st.dialog("Edit mission")
def edit_mission(pmo_table: PMOTable, current_project: ProjectDTO, current_mission: MissionDTO):

    with st.form(key="edit_mission_form", clear_on_submit=False, enter_to_submit=True):

        # Store original status before changes
        original_status = current_mission.status
        # Store original name before changes
        original_name = current_mission.mission_name

        # Add fields for mission details with existing values
        mission_name, mission_referee, team_members, start_date, end_date, status, priority, progress = get_fields_mission(
            pmo_table=pmo_table, mission=current_mission)

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
            current_mission.mission_referee = mission_referee if mission_referee else ""
            current_mission.team_members = team_members
            current_mission.start_date = start_date
            current_mission.end_date = end_date
            current_mission.status = status
            current_mission.priority = priority
            current_mission.progress = progress

            if current_project.global_follow_up_mission_id != "":
                # If the project has a Global Follow-up mission, we update its milestones
                # to include the new mission name
                global_follow_up_mission = ProjectPlanDTO.get_mission_by_id(
                    pmo_table.data, current_project.global_follow_up_mission_id)
                if global_follow_up_mission:
                    for milestone in global_follow_up_mission.milestones:
                        if milestone.name == original_name:
                            # If the milestone already exists, we modify its name to the new one
                            milestone.name = current_mission.mission_name
                            break

            pmo_table.commit_and_save()
            # We delete the tree-menu state to remove data concerning the tree
            # So at the next rerun, the tree will be rebuilt and we can set default values
            pmo_table.pmo_state.reset_tree_pmo()

            st.rerun()


@st.dialog("Edit client")
def edit_client(pmo_table: PMOTable, current_client: ClientDTO):
    with st.form(key="edit_client_form", clear_on_submit=False, enter_to_submit=True):
        existing_client_name = current_client.client_name
        # Add fields for client details
        client_name = st.text_input("Insert your client name", value=existing_client_name)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Check if the client name is the same as previously
            # If so, do nothing and return
            if client_name == existing_client_name:
                return

            check_client_name_unique_and_not_empty(client_name, pmo_table)

            # Update client name
            pmo_table.update_client_name_by_id(current_client.id, client_name)
            pmo_table.commit_and_save()
            # Update folder names in the space if needed
            update_folders_names(current_client)
            # We delete the tree-menu state to remove data concerning the tree
            # So at the next rerun, the tree will be rebuilt and we can set default values
            pmo_table.pmo_state.reset_tree_pmo()
            st.rerun()


@st.dialog("Edit project")
def edit_project(pmo_table: PMOTable, current_client: ClientDTO, current_project: ProjectDTO):

    with st.form(key="edit_project_form", clear_on_submit=False, enter_to_submit=True):
        existing_project_name = current_project.name
        existing_client_name = current_client.client_name
        # Add fields for project details
        client_name = st.text_input("Insert your client name", value=existing_client_name)
        project_name = st.text_input("Insert your project name", value=existing_project_name)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Check if the project name is the same as previously
            # If so, do nothing and return
            if project_name == existing_project_name and client_name == existing_client_name:
                return

            if check_set_client_and_project_name_unique_and_not_empty(client_name, project_name, pmo_table):
                return

            # Update client name
            pmo_table.update_client_name_by_id(current_client.id, client_name)
            # Update project name
            pmo_table.update_project_name_by_id(current_project.id, project_name)

            pmo_table.commit_and_save()

            # Update folder names in the space if needed
            update_folders_names(current_client, current_project)
            # We delete the tree-menu state to remove data concerning the tree
            # So at the next rerun, the tree will be rebuilt and we can set default values
            pmo_table.pmo_state.reset_tree_pmo()

            st.rerun()


def update_folders_names(current_client: ClientDTO, current_project: ProjectDTO = None):
    with StreamlitAuthenticateUser():
        # Update folder names in the space if needed
        space_service = SpaceService.get_instance()
        current_folder_root_id = current_client.folder_root_id
        if current_folder_root_id != "":
            # Update the root folder name in the space
            new_folder = ExternalSpaceCreateFolder(
                name=current_client.client_name)
            space_service.update_folder(current_folder_root_id, new_folder)
        if not current_project:
            return
        current_folder_project_id = current_project.folder_project_id
        if current_folder_project_id == "":
            return
        # We parse value to ensure it is a valid tag format because auto parse is not longer availaible
        # for values in lab
        current_client_name = current_client.client_name
        current_client_name = Tag.parse_tag(current_client_name)
        new_folder = ExternalSpaceCreateFolder(
            name=current_project.name,
            tags=[Tag(key="type", value="client", auto_parse=True),
                  Tag(key="client", value=current_client_name,
                      auto_parse=True)])
        space_service.update_folder(current_folder_project_id, new_folder)


@st.dialog("Edit milestone")
def edit_milestone(pmo_table: PMOTable, milestone_id: str):
    milestone = ProjectPlanDTO.get_milestone_by_id(pmo_table.data, milestone_id)
    mission = ProjectPlanDTO.get_mission_by_milestone_id(pmo_table.data, milestone_id)
    project = ProjectPlanDTO.get_project_by_mission_id(pmo_table.data, mission.id)
    client = ProjectPlanDTO.get_client_by_project_id(pmo_table.data, project.id)
    previous_milestone_done = milestone.done
    with st.form(key="edit_milestone_form", clear_on_submit=False, enter_to_submit=True):
        # Add fields for milestone details with existing values
        milestone_name, milestone_done = get_fields_milestone(milestone=milestone)

        submit_button = st.form_submit_button(label="Submit")

        if submit_button:
            # Update the milestone data
            milestone.name = milestone_name
            milestone.done = milestone_done
            if previous_milestone_done == False and milestone.done == True:
                # We send a notification to the users of the mission
                pmo_table.send_notification_milestone_done_to_team_members(milestone)

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
            mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, mission_id)
            if mission:
                mission.milestones.append(new_milestone)
            pmo_table.commit_and_save()
            st.rerun()


@st.dialog("Add project")
def add_project(pmo_table: PMOTable, current_client: ClientDTO):
    with st.form(clear_on_submit=False, enter_to_submit=True, key="project_form"):
        name_project = st.text_input("Insert your project name")

        submit_button = st.form_submit_button(
            label="Submit"
        )

        if submit_button:
            if check_set_client_and_project_name_unique_and_not_empty(
                    current_client.client_name, name_project, pmo_table):
                return

            # Create new project using DTO
            new_project = ProjectDTO(
                id=StringHelper.generate_uuid(),
                name=name_project,
                missions=[],
                folder_project_id="",
                global_follow_up_mission_id=""
            )

            if pmo_table.data_settings.create_folders_in_space:
                create_subfolders_in_space(pmo_table, current_client, new_project)

            if pmo_table.get_create_folders_in_space():
                # Create a mission "Global Follow-up" : this mission will be used to track the global follow-up of the project
                # and to update the status of the project (tags on folders)
                global_follow_up_mission_id = StringHelper.generate_uuid()
                global_follow_up_mission = MissionDTO(
                    id=global_follow_up_mission_id,
                    mission_name="Global Follow-up",
                    mission_referee="",
                    team_members=[],
                    start_date=datetime.now().strftime("%Y-%m-%d"),
                    end_date=None,
                    milestones=[],
                    status=Status.IN_PROGRESS.value,
                    priority=Priority.NONE.value,
                    progress=0.0
                )
                new_project.global_follow_up_mission_id = global_follow_up_mission_id
                new_project.missions.append(global_follow_up_mission)
                pmo_table.pmo_state.set_current_mission(global_follow_up_mission)

            current_client.projects.append(new_project)

            # Save
            pmo_table.commit_and_save()
            # Set success message in session state
            pmo_table.pmo_state.set_show_success_project_created(True)
            pmo_table.pmo_state.set_current_project(new_project)
            # We delete the tree-menu state to remove data concerning the tree
            # So at the next rerun, the tree will be rebuilt and we can set default values
            pmo_table.pmo_state.reset_tree_pmo()
            st.rerun()


@st.dialog("Add client")
def add_client(pmo_table: PMOTable):
    with st.form(clear_on_submit=False, enter_to_submit=True, key="project_form"):
        client_name = st.text_input("Insert your client name")

        submit_button = st.form_submit_button(
            label="Submit"
        )

        if submit_button:
            if check_client_name_unique_and_not_empty(client_name, pmo_table):
                return

            new_client = ClientDTO(
                id=StringHelper.generate_uuid(),
                client_name=client_name,
                projects=[],
                folder_root_id="",
            )

            if pmo_table.data_settings.create_folders_in_space:
                # Create root folders in the space with the client name
                create_root_folder_in_space(pmo_table, new_client)

            pmo_table.data.data.append(new_client)

            # Save
            pmo_table.commit_and_save()
            # Set success message in session state
            pmo_table.pmo_state.set_show_success_client_created(True)
            pmo_table.pmo_state.set_current_client(new_client)
            # We delete the tree-menu state to remove data concerning the tree
            # So at the next rerun, the tree will be rebuilt and we can set default values
            pmo_table.pmo_state.reset_tree_pmo()
            st.rerun()


@st.dialog("Move milestone up")
def move_milestone_up(pmo_table: PMOTable, mission_id: str, milestone_id: str) -> None:
    """
    Move a milestone up in the list (swap with the previous one)

    Args:
        pmo_table: The PMO table
        mission_id: ID of the mission containing the milestone
        milestone_id: ID of the milestone to move
    """
    with st.form(clear_on_submit=False, enter_to_submit=True, key="move_up_form"):
        st.write("Move the milestone up in the list?")

        submit_button = st.form_submit_button(
            label="Move up"
        )

        if submit_button:
            # Find the mission and its milestones
            mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, mission_id)
            if not mission or not mission.milestones:
                return

            # Find the milestone index
            try:
                idx = next(i for i, m in enumerate(mission.milestones) if m.id == milestone_id)
            except StopIteration:
                return

            # If it's already at the top, do nothing
            if idx == 0:
                return

            # Swap with the previous milestone
            mission.milestones[idx], mission.milestones[idx-1] = mission.milestones[idx-1], mission.milestones[idx]
            pmo_table.commit_and_save()
            st.rerun()


@st.dialog("Move milestone down")
def move_milestone_down(pmo_table: PMOTable, mission_id: str, milestone_id: str) -> None:
    """
    Move a milestone down in the list (swap with the next one)

    Args:
        pmo_table: The PMO table
        mission_id: ID of the mission containing the milestone
        milestone_id: ID of the milestone to move
    """
    with st.form(clear_on_submit=False, enter_to_submit=True, key="move_down_form"):
        st.write("Move the milestone down in the list?")
        submit_button = st.form_submit_button(
            label="Move down"
        )

        if submit_button:
            # Find the mission and its milestones
            mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, mission_id)
            if not mission or not mission.milestones:
                return

            # Find the milestone index
            try:
                idx = next(i for i, m in enumerate(mission.milestones) if m.id == milestone_id)
            except StopIteration:
                return

            # If it's already at the bottom, do nothing
            if idx == len(mission.milestones) - 1:
                return

            # Swap with the next milestone
            mission.milestones[idx], mission.milestones[idx+1] = mission.milestones[idx+1], mission.milestones[idx]
            pmo_table.commit_and_save()
            st.rerun()
