from typing import List, Optional
from datetime import datetime, date
from pydantic import field_validator
from gws_core.core.model.model_dto import BaseModelDTO

class SettingsDTO(BaseModelDTO):
    """Represents the settings for the project plan"""
    create_folders_in_space: bool = False
    company_members: List[str] = []
    predefined_missions: List["MissionDTO"] = []


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


class ProjectDTO(BaseModelDTO):
    """Represents a project with its missions"""
    id: str
    name: str
    missions: List[MissionDTO]
    folder_project_id: str

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


class ClientDTO(BaseModelDTO):
    """Represents a client with its projects"""
    id : str
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
    def get_project_by_client_and_project_name(cls, project_plan: "ProjectPlanDTO", project_selected: str) -> Optional["ProjectDTO"]:
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
    def get_milestone_by_id(cls, project_plan: "ProjectPlanDTO", milestone_id: str) -> Optional["MilestoneDTO"]:
        for client in project_plan.data:
            for project in client.projects:
                for mission in project.missions:
                    milestone = MilestoneDTO.get_milestone_by_id(mission.milestones, milestone_id)
                    if milestone:
                        return milestone
        return None
