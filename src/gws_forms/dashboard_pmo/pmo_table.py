import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, List, Dict
from abc import abstractmethod
import pytz
from gws_forms.dashboard_pmo.pmo_state import PMOState
from gws_forms.dashboard_pmo.pmo_dto import SettingsDTO, ProjectPlanDTO, ProjectDTO, MissionDTO, MilestoneDTO
from gws_core import StringHelper
from gws_core.streamlit import StreamlitAuthenticateUser


class Event:
    def __init__(self, event_type: Literal['update_mission_progress'], data: Any = None):
        self.event_type = event_type  # Store the event type
        self.data = data


class MessageObserver:
    @abstractmethod
    def update(self, event: Event, current_project: ProjectDTO) -> bool:
        """Method called when a message is dispatched"""
        # This method is implemented in subclasses to update tags on folders when the project plan is saved
        pass

# Class to define the different status


class Status(Enum):
    NONE = "No status"
    IN_PROGRESS = "📈 In progress"
    TODO = "📝 Todo"
    DONE = "✅ Done"
    CLOSED = "☑️ Closed"

    @classmethod
    def get_order(cls) -> Dict[str, int]:
        """
        Define the custom order for the "status" column
        Return the order of the status
        """
        order = {
            cls.IN_PROGRESS.value: 0,
            cls.TODO.value: 1,
            cls.DONE.value: 2,
            cls.CLOSED.value: 3,
            cls.NONE.value: 4
        }
        return order

    @classmethod
    def get_values(cls) -> List[str]:
        """
        Get all status values as a list
        Return the status values
        """
        return [status.value for status in cls]

# Class to define the different priorities


class Priority(Enum):
    NONE = "No priority"
    HIGH = "🔴 High"
    MEDIUM = "🟡 Medium"
    LOW = "🟢 Low"

    @classmethod
    def get_colors(cls) -> Dict:
        """
        Define the custom colors for the "Priority" column
        Colors are used in the plot overview tab
        Return the colors of the priority
        """
        colors = {
            cls.HIGH.value: "#ff4c4c",
            cls.MEDIUM.value: "#f2eb1d",
            cls.LOW.value: "#59d95e",
            cls.NONE.value: "#808080"
        }
        return colors

    @classmethod
    def get_values(cls) -> List[str]:
        """
        Get all priorities values as a list
        Return the priority values
        """
        return [priority.value for priority in cls]


class PMOTable:
    # Define columns names
    NAME_COLUMN_START_DATE = 'Start Date'
    NAME_COLUMN_END_DATE = 'End Date'
    NAME_COLUMN_MILESTONES = 'Milestones'
    NAME_COLUMN_PRIORITY = 'Priority'
    NAME_COLUMN_PROGRESS = 'Progress (%)'
    NAME_COLUMN_PROJECT_NAME = 'Project Name'
    NAME_COLUMN_CLIENT_NAME = 'Client Name'
    NAME_COLUMN_MISSION_NAME = 'Mission Name'
    NAME_COLUMN_MISSION_REFEREE = 'Mission Referee'
    NAME_COLUMN_TEAM_MEMBERS = 'Team Members'
    NAME_COLUMN_STATUS = "Status"

    folder_project_plan: str
    folder_details: str
    missions_order: List
    folder_change_log: str
    observer: Optional[MessageObserver]
    data: ProjectPlanDTO
    pmo_state: PMOState
    selected_file: str
    file_path_change_log: str
    folder_settings: str

    def __init__(self, folder_project_plan=None, folder_details=None, missions_order=None,
                 folder_change_log=None, folder_settings = None, observer=None, selected_file=None):
        """
        Initialize the PMOTable object with the data file containing the project missions.
        Functions will define the actions to perform with the PMO table in order to see them in the dashboard
        """
        self.folder_project_plan = folder_project_plan
        self.folder_settings = folder_settings
        self.selected_file = selected_file
        self.observer = observer
        self.folder_details = folder_details
        self.folder_change_log = folder_change_log
        if folder_change_log:
            self.file_path_change_log = os.path.join(
                self.folder_change_log, 'change_log.json')
            if not os.path.exists(self.file_path_change_log):
                with open(self.file_path_change_log, 'w', encoding="utf-8") as f:
                    f.write("[]")
        else:
            self.file_path_change_log = None

        self.pmo_state = PMOState(self.file_path_change_log)
        self.data_settings = self.load_settings_data_from_json()

        if missions_order is None:
            self.missions_order = []
            if self.pmo_state.get_predefined_missions():
                for mission in self.pmo_state.get_predefined_missions():
                    self.missions_order.append(mission.mission_name)
                self.missions_order = self.pmo_state.get_predefined_missions()
        else:
            self.missions_order = missions_order
        self.data = self.load_pmo_data()
        self.save_settings()
        self.commit_and_save()

        # Persist initial value to session state
        self.pmo_state.set_create_folders_in_space_value(self.data_settings.create_folders_in_space)
        self.pmo_state.set_company_members(self.data_settings.company_members)
        self.pmo_state.set_predefined_missions(self.data_settings.predefined_missions)

    def save_settings(self) -> None:
        """
        Set the settings for the PMOTable.
        Set the parameter create folder in space
        Set the company members
        """
        path_json = os.path.join(self.folder_settings, f"settings.json")
        data_dict = self.data_settings.to_json_dict()
        with open(path_json, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2)

    def load_pmo_settings_from_example(self):
        # Initialize example settings data
        data = SettingsDTO(create_folders_in_space = True,
                           company_members=[],
                           predefined_missions=[])
        return data

    def load_settings_data_from_json(self):
        """Load PMO settings data from file or create new if none exists
        """
        file = [f for f in os.listdir(self.folder_settings) if f.endswith(".json")]

        if file:
            settings_file = os.path.join(self.folder_settings, file[0])
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                # Convert raw data to ProjectPlanDTO
                return SettingsDTO.from_json(loaded_data)
        else:
            return self.load_pmo_settings_from_example()

    def load_pmo_data(self):
        if self.folder_project_plan:
            data = self.load_pmo_data_from_json()
        else:
            data = self.load_pmo_data_from_example()
        return data

    def load_pmo_data_from_example(self):
        # Initialize example data if no folder_project_plan is provided
        example_milestone = MilestoneDTO(
            id=StringHelper.generate_uuid(),
            name="step 1",
            done=False
        )
        example_mission = MissionDTO(
            mission_name="Mission 1",
            mission_referee=self.pmo_state.get_list_lab_users()[0],
            team_members=[self.pmo_state.get_list_lab_users()[0]],
            start_date=datetime.now(tz=pytz.timezone('Europe/Paris')).strftime("%d %m %Y"),
            end_date=None,
            milestones=[example_milestone],
            status=Status.TODO.value,
            priority=Priority.HIGH.value,
            progress=0,
            id=StringHelper.generate_uuid()
        )
        example_project = ProjectDTO(
            id=StringHelper.generate_uuid(),
            client_name ="Client 1",
            name="Project 1",
            missions=[example_mission],
            folder_root_id="",
            folder_project_id=""
        )
        # Default to True for new example data
        return ProjectPlanDTO(data=[example_project])

    def load_pmo_data_from_json(self):
        """Load PMO data from file or create new if none exists
            Get the last pmo_project_plan by default

        Args:
            selected_file: Optional specific file to load, if None loads most recent

        Returns:
            PMOTable: Updated PMO table and success flag"""

        # List all JSON files in the saved directory
        files = sorted([f.split(".json")[0] for f in os.listdir(self.folder_project_plan)
                        if f.endswith(".json")], reverse=True)

        if not files:
            return self.load_pmo_data_from_example()

        selected_file = self.selected_file + ".json" if self.selected_file else files[0] + ".json"
        file_path = os.path.join(
            self.folder_project_plan, selected_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            # Convert raw data to ProjectPlanDTO
            return ProjectPlanDTO.from_json(loaded_data)

    def apply_observer_update_mission_progress(self, current_project: ProjectDTO) -> None:
        # Apply the observer -> Update tag folder
        if self.observer:
            check = self.observer.update(Event(event_type='update_mission_progress'), current_project)
            if not check:
                raise Exception("Something got wrong, close the app and try again.")

    def log_status_change(self, mission_id: str, project_name: str, mission_name: str,
                          old_status: str, new_status: str) -> None:
        """
        Log a status change for a mission

        Args:
            mission_id: ID of the mission
            project_name: Name of the project
            mission_name: Name of the mission
            old_status: Previous status
            new_status: New status
        """
        new_entry = {
            "mission_id": mission_id,
            "project": project_name,
            "mission": mission_name,
            "status_before": old_status,
            "status_after": new_status,
            "date": datetime.now().isoformat()
        }
        self.pmo_state.append_status_change_log(new_entry)

    def update_mission_statuses_and_progress(self) -> None:
        """Ensures required fields are present and have correct types.
        Auto-updates progress, status and dates based on conditions."""
        formatted_date = datetime.now().date()

        # Process each project and its missions
        for project in self.data.data:
            for mission in project.missions:
                # Set end date if status is DONE and no end date exists
                if mission.status == Status.DONE.value and not mission.end_date:
                    mission.end_date = formatted_date

                # Calculate progress based on milestones
                if mission.milestones:
                    total_steps = len(mission.milestones)
                    completed_steps = sum(1 for m in mission.milestones if m.done)
                    mission.progress = round((completed_steps / total_steps) * 100, 2) if total_steps > 0 else 0.0

                # Auto-set status to DONE if progress is 100%
                if (mission.progress == 100 and
                        mission.status in [Status.IN_PROGRESS.value, Status.TODO.value, Status.NONE.value]):
                    old_status = mission.status
                    mission.status = Status.DONE.value
                    if not mission.end_date:
                        mission.end_date = formatted_date

                    # Log status change
                    self.log_status_change(mission.id, project.name, mission.mission_name, old_status, mission.status)

                # Auto-set status to in progress if progress is more than 0% and status is none or todo
                if (mission.progress != 0 and
                        mission.status in [Status.TODO.value, Status.NONE.value]):
                    old_status = mission.status
                    mission.status = Status.IN_PROGRESS.value
                    if not mission.start_date:
                        mission.start_date = formatted_date

                    # Log status change
                    self.log_status_change(mission.id, project.name, mission.mission_name, old_status, mission.status)

        # Handle mission order dependencies
        if self.missions_order:
            # Process each mission except the last one
            for idx, mission_name in enumerate(self.missions_order[:-1]):
                next_mission_name = self.missions_order[idx + 1]

                # Find completed missions and their projects
                for project in self.data.data:
                    current_mission = next((m for m in project.missions if m.mission_name ==
                                            mission_name and m.status == Status.DONE.value), None)
                    if current_mission:
                        # Find and update next mission in sequence
                        next_mission = next(
                            (m for m in project.missions if m.mission_name == next_mission_name),
                            None
                        )
                        if next_mission:
                            if not next_mission.start_date:
                                next_mission.start_date = formatted_date
                            if next_mission.status == Status.TODO.value:
                                old_status = next_mission.status
                                next_mission.status = Status.IN_PROGRESS.value

                                # Log status change
                                self.log_status_change(next_mission.id, project.name,
                                                       next_mission.mission_name, old_status, next_mission.status)

        # Convert any accumulated log entries to JSON
        if self.pmo_state.get_status_change_log():
            self.pmo_state.convert_log_to_json()

        # Apply the observer -> Update tag folder if a external observer is set
        for project in self.data.data:
            self.apply_observer_update_mission_progress(project)

    def update_milestone_status_by_id(self, milestone_id: str, done: bool) -> None:
        """
        Update the status of a milestone by its ID.

        Args:
            milestone_id: The ID of the milestone to update.
            done: The new status of the milestone (True if done, False otherwise).
        """
        milestone = ProjectPlanDTO.get_milestone_by_id(self.data, milestone_id)
        milestone.done = done

    def update_project_name_by_id(self, project_id: str, project_name: str) -> None:
        """
        Update the name of a project by its ID.

        Args:
            project_id: The ID of the project to update.
            project_name: The new name for the project.
        """
        project = ProjectPlanDTO.get_project_by_id(self.data, project_id)
        project.name = project_name

    def update_client_name_by_id(self, project_id: str, client_name: str) -> None:
        """
        Update the name of a client by its ID.

        Args:
            project_id: The ID of the project to update.
            client_name: The new name for the project.
        """
        project = ProjectPlanDTO.get_project_by_id(self.data, project_id)
        project.client = client_name

    def save_data_in_folder(self) -> None:
        """Save data as JSON using DTOs"""
        timestamp = datetime.now().strftime("plan_%Y-%m-%d-%Hh%M")
        path_json = os.path.join(self.folder_project_plan, f"{timestamp}.json")
        data_dict = self.data.to_json_dict()
        with open(path_json, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2)

    def commit_and_save(self):
        with StreamlitAuthenticateUser():
            self.update_mission_statuses_and_progress()
            # Save changes
            self.save_data_in_folder()

    def set_create_folders_in_space(self, value: bool) -> None:
        """
        Set the create_folders_in_space attribute in settings DTO and persist it.
        """
        self.data_settings.create_folders_in_space = value
        self.pmo_state.set_create_folders_in_space_value(value)
        self.save_settings()

    def get_create_folders_in_space(self) -> bool:
        """
        Get the create_folders_in_space attribute from settings DTO.
        """
        return bool(getattr(self.data_settings, "create_folders_in_space", True))

    def set_company_members(self, members: list) -> None:
        """
        Set the company_members attribute in settings DTO and persist it.
        """
        self.data_settings.company_members = members
        self.pmo_state.set_company_members(members)
        self.save_settings()

    def get_company_members(self) -> list:
        """
        Get the company_members attribute from settings DTO.
        """
        return getattr(self.data_settings, "company_members", self.pmo_state.get_list_lab_users())

    def set_predefined_missions(self, missions: list) -> None:
        """
        Set the predefined_missions attribute in settings DTO and persist it.
        """
        self.data_settings.predefined_missions = missions
        self.pmo_state.set_predefined_missions(missions)
        self.save_settings()

    def get_predefined_missions(self) -> list:
        """
        Get the predefined_missions attribute from settings DTO.
        """
        return getattr(self.data_settings, "predefined_missions", self.pmo_state.get_predefined_missions())
