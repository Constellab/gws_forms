from datetime import date, datetime
from typing import List, Optional

from gws_core import BaseModelDTO
from pydantic import field_validator


class UserDTO(BaseModelDTO):
    """DTO for user information"""
    first_name: str
    id: Optional[str] = None


class SettingsDTO(BaseModelDTO):
    """Represents the settings for the project plan"""
    create_folders_in_space: bool = False
    company_members: List["UserDTO"] = []
    predefined_missions: List["MissionDTO"] = []
    share_folders_with_team: str = ""


class MilestoneDTO(BaseModelDTO):
    """Represents a single milestone in a mission"""
    id: str
    name: str
    done: bool = False

    @classmethod
    def get_milestone_by_id(cls, milestones: List["MilestoneDTO"], milestone_id: str) -> Optional["MilestoneDTO"]:
        """
        Get milestone by its ID
        Args:
            milestones: List of MilestoneDTO objects
            milestone_id: ID of the milestone to find
        Returns:
            MilestoneDTO: Milestone object if found, None otherwise
        """
        return next((milestone for milestone in milestones if milestone.id == milestone_id), None)


class MissionDTO(BaseModelDTO):
    """Represents a single mission within a project"""
    mission_name: str
    mission_referee: str
    team_members: List[str]
    start_date: Optional[date]
    end_date: Optional[date]
    milestones: List[MilestoneDTO]
    status: str
    priority: str
    progress: float
    id: str

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def validate_date(cls, value):
        if isinstance(value, str) and value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                try:
                    return datetime.strptime(value, "%d %m %Y").date()
                except ValueError:
                    return None
        elif isinstance(value, date):
            return value
        return None

    @classmethod
    def get_mission_by_id(cls, missions: List["MissionDTO"], mission_id: str) -> Optional["MissionDTO"]:
        """
        Get mission by its ID
        Args:
            missions: List of MissionDTO objects
            mission_id: ID of the mission to find
        Returns:
            MissionDTO: Mission object if found, None otherwise
        """
        return next((mission for mission in missions if mission.id == mission_id), None)

    @classmethod
    def get_earlier_start_date(cls, missions: List["MissionDTO"]) -> Optional[date]:
        """
        Get the earliest start date from a list of missions
        Args:
            missions: List of MissionDTO objects
        Returns:
            date: Earliest start date if found, None otherwise
        """
        earliest_date = None
        for mission in missions:
            if mission.start_date:
                if earliest_date is None or mission.start_date < earliest_date:
                    earliest_date = mission.start_date
        return earliest_date

    @classmethod
    def get_latest_end_date(cls, missions: List["MissionDTO"]) -> Optional[date]:
        """
        Get the latest end date from a list of missions
        Args:
            missions: List of MissionDTO objects
        Returns:
            date: Latest end date if found, None otherwise
        """
        latest_date = None
        for mission in missions:
            if mission.end_date:
                if latest_date is None or mission.end_date > latest_date:
                    latest_date = mission.end_date
        return latest_date

    @classmethod
    def get_average_status(cls, missions: List["MissionDTO"]) -> str:
        """
        Calculate the average status of all missions :
        If all is done, return done
        If all is closed, return closed
        If there is at least one mission in progress, return in progress
        If there is at least one mission in todo, return todo
        else return ""
        Args:
            missions: List of MissionDTO objects
        Returns:
            status: Average status of the missions
        """
        statuses = {mission.status for mission in missions}
        if "✅ Done" in statuses and len(statuses) == 1:
            return "✅ Done"
        elif "☑️ Closed" in statuses and len(statuses) == 1:
            return "☑️ Closed"
        elif "📈 In progress" in statuses:
            return "📈 In progress"
        elif "📝 Todo" in statuses:
            return "📝 Todo"
        else:
            return ""

    @classmethod
    def get_average_progress(cls, missions: List["MissionDTO"]) -> float:
        """
        Calculate the average progress of all missions
        Args:
            missions: List of MissionDTO objects
        Returns:
            float: Average progress of the missions
        """
        if not missions:
            return 0.0
        total_progress = sum(mission.progress for mission in missions)
        return total_progress / len(missions) if len(missions) > 0 else 0.0


class ProjectDTO(BaseModelDTO):
    """Represents a project with its missions"""
    id: str
    name: str
    missions: List[MissionDTO]
    folder_project_id: str
    global_follow_up_mission_id: Optional[str]

    @classmethod
    def get_mission_of_a_project_by_name(cls, project: "ProjectDTO", mission_name: str) -> Optional[str]:
        for mission in project.missions:
            if mission.mission_name == mission_name:
                return mission
        return None

    @classmethod
    def get_project_by_id(cls, projects: List["ProjectDTO"], project_id: str) -> Optional["ProjectDTO"]:
        """
        Get project by its ID
        Args:
            projects: List of ProjectDTO objects
            project_id: ID of the project to find
        Returns:
            ProjectDTO: Project object if found, None otherwise
        """
        return next((project for project in projects if project.id == project_id), None)

    @classmethod
    def get_earlier_start_date(cls, projects: List["ProjectDTO"]) -> Optional[date]:
        """
        Get the earliest start date from all missions in all projects
        Args:
            projects: List of ProjectDTO objects
        Returns:
            date: Earliest start date if found, None otherwise
        """
        earliest_date = None
        for project in projects:
            for mission in project.missions:
                if mission.start_date:
                    if earliest_date is None or mission.start_date < earliest_date:
                        earliest_date = mission.start_date
        return earliest_date

    @classmethod
    def get_latest_end_date(cls, projects: List["ProjectDTO"]) -> Optional[date]:
        """
        Get the latest end date from all missions in all projects
        Args:
            projects: List of ProjectDTO objects
        Returns:
            date: Latest end date if found, None otherwise
        """
        latest_date = None
        for project in projects:
            for mission in project.missions:
                if mission.end_date:
                    if latest_date is None or mission.end_date > latest_date:
                        latest_date = mission.end_date
        return latest_date

    @classmethod
    def get_average_status(cls, projects: List["ProjectDTO"]) -> str:
        """
        Calculate the average status of all projects:
        If all are done, return done
        If all are closed, return closed
        If there is at least one project in progress, return in progress
        If there is at least one project in todo, return todo
        else return ""
        Args:
            projects: List of ProjectDTO objects
        Returns:
            status: Average status of the projects
        """
        statuses = {mission.status for project in projects for mission in project.missions}
        if "✅ Done" in statuses and len(statuses) == 1:
            return "✅ Done"
        elif "☑️ Closed" in statuses and len(statuses) == 1:
            return "☑️ Closed"
        elif "📈 In progress" in statuses:
            return "📈 In progress"
        elif "📝 Todo" in statuses:
            return "📝 Todo"
        else:
            return ""

    @classmethod
    def get_average_progress(cls, projects: List["ProjectDTO"]) -> float:
        """
        Calculate the average progress of all projects
        Args:
            projects: List of ProjectDTO objects
        Returns:
            float: Average progress of the projects
        """
        if not projects:
            return 0.0
        total_progress = sum(mission.progress for project in projects for mission in project.missions)
        total_missions = sum(len(project.missions) for project in projects)
        return total_progress / total_missions if total_missions > 0 else 0.0


class ClientDTO(BaseModelDTO):
    """Represents a client with its projects"""
    id: str
    client_name: str
    projects: List[ProjectDTO]
    folder_root_id: str

    @classmethod
    def get_project_by_id(cls, clients: List["ClientDTO"], project_id: str) -> Optional[ProjectDTO]:
        for client in clients:
            for project in client.projects:
                if project.id == project_id:
                    return project
        return None

    @classmethod
    def get_client_by_name(cls, clients: List["ClientDTO"], client_name: str) -> Optional["ClientDTO"]:
        for client in clients:
            if client.client_name == client_name:
                return client
        return None


class ProjectPlanDTO(BaseModelDTO):
    """Root structure for the project plan data"""
    data: List["ClientDTO"]

    @classmethod
    def get_clients(cls, project_plan: "ProjectPlanDTO") -> List["ClientDTO"]:
        return project_plan.data

    @classmethod
    def get_projects(cls, project_plan: "ProjectPlanDTO") -> List["ProjectDTO"]:
        projects = []
        for client in project_plan.data:
            projects.extend(client.projects)
        return projects

    @classmethod
    def get_project_by_id(cls, project_plan: "ProjectPlanDTO", project_id: str) -> Optional["ProjectDTO"]:
        for client in project_plan.data:
            for project in client.projects:
                if project.id == project_id:
                    return project
        return None

    @classmethod
    def get_client_by_id(cls, project_plan: "ProjectPlanDTO", client_id: str) -> Optional["ClientDTO"]:
        for client in project_plan.data:
            if client.id == client_id:
                return client
        return None

    @classmethod
    def get_project_by_client_and_project_name(
            cls, project_plan: "ProjectPlanDTO", project_selected: str) -> Optional["ProjectDTO"]:
        client_name = project_selected.split(" ⸱ ")[0]
        project_name = project_selected.split(" ⸱ ")[1]
        for client in project_plan.data:
            if client.client_name == client_name:
                for project in client.projects:
                    if project.name == project_name:
                        return project
        return None

    @classmethod
    def get_mission_by_id(cls, project_plan: "ProjectPlanDTO", mission_id: str) -> Optional["MissionDTO"]:
        for client in project_plan.data:
            for project in client.projects:
                mission = MissionDTO.get_mission_by_id(project.missions, mission_id)
                if mission:
                    return mission
        return None

    @classmethod
    def get_project_by_mission_id(cls, project_plan: "ProjectPlanDTO", mission_id: str) -> Optional["ProjectDTO"]:
        for client in project_plan.data:
            for project in client.projects:
                for mission in project.missions:
                    if mission.id == mission_id:
                        return project
        return None

    @classmethod
    def get_client_by_project_id(cls, project_plan: "ProjectPlanDTO", project_id: str) -> Optional["ClientDTO"]:
        for client in project_plan.data:
            for project in client.projects:
                if project.id == project_id:
                    return client
        return None

    @classmethod
    def get_milestone_by_id(cls, project_plan: "ProjectPlanDTO", milestone_id: str) -> Optional["MilestoneDTO"]:
        for client in project_plan.data:
            for project in client.projects:
                for mission in project.missions:
                    milestone = MilestoneDTO.get_milestone_by_id(mission.milestones, milestone_id)
                    if milestone:
                        return milestone
        return None

    @classmethod
    def get_mission_by_milestone_id(cls, project_plan: "ProjectPlanDTO", milestone_id: str) -> Optional["MissionDTO"]:
        for client in project_plan.data:
            for project in client.projects:
                for mission in project.missions:
                    for milestone in mission.milestones:
                        if milestone.id == milestone_id:
                            return mission
        return None
