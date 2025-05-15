from typing import List, Optional
from datetime import datetime, date
from pydantic import Field, field_validator
from gws_core.core.model.model_dto import BaseModelDTO


class MilestoneDTO(BaseModelDTO):
    """Represents a single milestone in a mission"""
    name: str
    done: bool = False


class MissionDTO(BaseModelDTO):
    """Represents a single mission within a project"""
    mission_name: str
    mission_referee: str
    team_members: List[str]
    start_date: Optional[str]
    end_date: Optional[str]
    milestones: List[MilestoneDTO]
    status: str
    priority: str
    progress: float
    id: str

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def validate_date(cls, value):
        if isinstance(value, date):
            return value.isoformat()
        return value


class ProjectDTO(BaseModelDTO):
    """Represents a project with its missions"""
    id: str
    name: str
    missions: List[MissionDTO]


class ProjectPlanDTO(BaseModelDTO):
    """Root structure for the project plan data"""
    data: List[ProjectDTO]
    column_types: dict

    @classmethod
    def get_project_id_by_name(cls, projects: "ProjectPlanDTO", project_name: str) -> Optional[str]:
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
                return project.id
        return None

    @classmethod
    def get_mission_id_by_name(cls, projects: "ProjectPlanDTO", project_id: str, mission_name: str) -> Optional[str]:
        """
        Get mission ID by its name
        Args:
            projects: ProjectPlanDTO object containing the list of projects
            project_name: Name of the project to find
            mission_name: Name of the mission to find
        Returns:
            str: Project ID if found, None otherwise
        """
        for project in projects.data:
            if project.id == project_id:
                for mission in project.missions:
                    if mission.mission_name == mission_name:
                        return mission.id
        return None
