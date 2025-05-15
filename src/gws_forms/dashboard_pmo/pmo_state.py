import os
import json
from typing import List
import streamlit as st
import pandas as pd

from gws_forms.dashboard_pmo.pmo_dto import ProjectDTO, MissionDTO


class PMOState():

    STATUS_CHANGE_LOG_KEY = "status_change_log"
    STATUS_CHANGE_JSON_KEY = "status_change_json"
    SHOW_SUCCESS_PROJECT_CREATED_KEY = "show_success_project_created"
    SHOW_SUCCESS_PROJECT_DELETED_KEY = "show_success_project_deleted"
    SHOW_SUCCESS_MISSION_DELETED_KEY = "show_success_mission_deleted"
    SHOW_SUCCESS_MISSION_ADDED_KEY = "show_success_mission_added"
    CURRENT_PROJECT_KEY = "current_project"
    CURRENT_MISSION_KEY = "current_mission"

    def __init__(self, file_path_change_log: str):
        self.file_path_change_log = file_path_change_log
        # Initialize a log list for status changes
        st.session_state[self.STATUS_CHANGE_LOG_KEY] = self.get_status_change_log()
        # Initialize a log list for status changes
        st.session_state[self.STATUS_CHANGE_JSON_KEY] = self.get_status_change_json()

    def get_current_project(self) -> str:
        return st.session_state.get(self.CURRENT_PROJECT_KEY, None)

    def set_current_project(self, project: ProjectDTO) -> None:
        st.session_state[self.CURRENT_PROJECT_KEY] = project

    def get_current_mission(self) -> str:
        return st.session_state.get(self.CURRENT_MISSION_KEY, None)

    def set_current_mission(self, mission: MissionDTO) -> None:
        st.session_state[self.CURRENT_MISSION_KEY] = mission

    # Show success
    def display_success_message(self) -> None:
        if self.get_show_success_project_created():
            st.toast("Project created successfully!", icon="✅")
            self.set_show_success_project_created(False)

        if self.get_show_success_delete_project():
            st.toast("Project deleted successfully!", icon="✅")
            self.set_show_success_delete_project(False)

        if self.get_show_success_delete_mission():
            st.toast("Mission deleted successfully!", icon="✅")
            self.set_show_success_delete_mission(False)

        if self.get_show_success_mission_added():
            st.toast("Mission added successfully!", icon="✅")
            self.set_show_success_mission_added(False)

    def get_show_success_project_created(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_PROJECT_CREATED_KEY, False)

    def set_show_success_project_created(self, boolean_success: bool) -> None:
        st.session_state[self.SHOW_SUCCESS_PROJECT_CREATED_KEY] = boolean_success

    def get_show_success_delete_project(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_PROJECT_DELETED_KEY, False)

    def set_show_success_delete_project(self, boolean_success: bool) -> None:
        st.session_state[self.SHOW_SUCCESS_PROJECT_DELETED_KEY] = boolean_success

    def get_show_success_delete_mission(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_MISSION_DELETED_KEY, False)

    def set_show_success_delete_mission(self, boolean_success: bool) -> None:
        st.session_state[self.SHOW_SUCCESS_MISSION_DELETED_KEY] = boolean_success

    def set_show_success_mission_added(self, boolean_success: bool) -> None:
        st.session_state[self.SHOW_SUCCESS_MISSION_ADDED_KEY] = boolean_success

    def get_show_success_mission_added(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_MISSION_ADDED_KEY, False)

    # Status change
    def get_status_change_json(self) -> List:
        if self.STATUS_CHANGE_JSON_KEY not in st.session_state or st.session_state[self.STATUS_CHANGE_JSON_KEY] == []:
            st.session_state[self.STATUS_CHANGE_JSON_KEY] = []
            if self.file_path_change_log and os.path.exists(self.file_path_change_log):
                with open(self.file_path_change_log, 'r', encoding="utf-8") as file:
                    content = file.read().strip()
                    if content:
                        st.session_state[self.STATUS_CHANGE_JSON_KEY] = json.loads(content)
        return st.session_state.get(self.STATUS_CHANGE_JSON_KEY)

    def append_status_change_json(self, value) -> None:
        st.session_state[self.STATUS_CHANGE_JSON_KEY].append(value)

    def get_status_change_log(self) -> List:
        return st.session_state.get(self.STATUS_CHANGE_LOG_KEY, [])

    def append_status_change_log(self, value) -> None:
        st.session_state[self.STATUS_CHANGE_LOG_KEY].append(value)

    def convert_log_to_json(self) -> None:
        if self.get_status_change_log():
            existing_logs = self.get_status_change_json()
            logs_to_add = [
                entry for entry in self.get_status_change_log()
                if entry not in existing_logs
            ]
            for entry in logs_to_add:
                self.append_status_change_json(entry)

            for entry in self.get_status_change_json():
                if isinstance(entry["status_before"], pd.Series):
                    entry["status_before"] = entry["status_before"].to_string()
            with open(self.file_path_change_log, 'w', encoding="utf-8") as f:
                f.write(json.dumps(self.get_status_change_json(),
                        indent=4, ensure_ascii=False))
