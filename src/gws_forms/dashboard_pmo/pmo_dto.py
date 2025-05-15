from typing import List, Optional
from datetime import datetime, date
from pydantic import field_validator
from gws_core.core.model.model_dto import BaseModelDTO


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
    folder_root_id: str
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


class ProjectPlanDTO(BaseModelDTO):
    """Root structure for the project plan data"""
    data: List[ProjectDTO]

    @classmethod
    def get_project_by_name(cls, projects: "ProjectPlanDTO", project_name: str) -> Optional[str]:
        """
        Get project ID by its name
        Args:
            projects: ProjectPlanDTO object containing the list of projects
            project_name: Name of the project to find
        Returns:
            str: Project ID if found, None otherwise
        """
        for project in projects.data:
            if project.name == project_name:
                return project
        return None

    @classmethod
    def get_mission_by_id(cls, projects: "ProjectPlanDTO", mission_id: str) -> Optional[MissionDTO]:
        """
        Get mission by its ID
        Args:
            projects: ProjectPlanDTO object containing the list of projects
            mission_id: ID of the mission to find
        Returns:
            MissionDTO: Mission object if found, None otherwise
        """
        for project in projects.data:
            mission = MissionDTO.get_mission_by_id(project.missions, mission_id)
            if mission:
                return mission
        return None

    @classmethod
    def get_project_by_id(cls, projects: "ProjectPlanDTO", project_id: str) -> Optional[ProjectDTO]:
        """
        Get project by its ID
        Args:
            projects: ProjectPlanDTO object containing the list of projects
            project_id: ID of the project to find
        Returns:
            ProjectDTO: Project object if found, None otherwise
        """
        return ProjectDTO.get_project_by_id(projects.data, project_id)

    @classmethod
    def get_milestone_by_id(cls, projects: "ProjectPlanDTO", milestone_id: str) -> Optional[MilestoneDTO]:
        """
        Get milestone by its ID within a specific mission
        Args:
            projects: ProjectPlanDTO object containing the list of projects
            mission_id: ID of the mission containing the milestone
            milestone_id: ID of the milestone to find
        Returns:
            MilestoneDTO: Milestone object if found, None otherwise
        """
        for project in projects.data:
            for mission in project.missions:
                milestone = MilestoneDTO.get_milestone_by_id(mission.milestones, milestone_id)
                if milestone:
                    return milestone
        return None
