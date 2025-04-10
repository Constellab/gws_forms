import os
import json
from typing import List
import streamlit as st
import pandas as pd

class PMOState():

    STATUS_CHANGE_LOG_KEY = "status_change_log"
    STATUS_CHANGE_JSON_KEY = "status_change_json"
    SHOW_SUCCESS_PROJECT_PLAN_KEY = "show_success_project_plan"
    SHOW_SUCCESS_TODO_KEY = "show_success_todo"
    SELECTED_REGEX_FILTER_PROJECT_NAME_KEY = "selected_regex_filter_project_name"
    SELECTED_REGEX_FILTER_MISSION_NAME_KEY = "selected_regex_filter_mission_name"
    SELECTED_MISSION_REFEREE_KEY = "selected_mission_referee"
    SELECTED_REGEX_FILTER_TEAM_MEMBERS_KEY = "selected_regex_filter_team_members"
    SELECTED_STATUS_KEY = "selected_status"
    SELECTED_PRIORITY_KEY ="selected_priority"

    def __init__(self, file_path_change_log : str):
        self.file_path_change_log = file_path_change_log
        # Initialize a log list for status changes
        st.session_state[self.STATUS_CHANGE_LOG_KEY] = self.get_status_change_log()
        # Initialize a log list for status changes
        st.session_state[self.STATUS_CHANGE_JSON_KEY] = self.get_status_change_json()

    ### Filters
    # Get the filters values
    def get_selected_regex_filter_project_name(self) -> str:
        #It's the value of text input selected_regex_filter_project_name
        return st.session_state.get(self.SELECTED_REGEX_FILTER_PROJECT_NAME_KEY, "")

    def get_selected_regex_filter_mission_name(self) -> str:
        #It's the value of text input selected_regex_filter_mission_name
        return st.session_state.get(self.SELECTED_REGEX_FILTER_MISSION_NAME_KEY, "")

    def get_selected_mission_referee(self) -> List:
        #It's the value of multiselect selected_mission_referee
        return st.session_state.get(self.SELECTED_MISSION_REFEREE_KEY, "")

    def get_selected_regex_filter_team_members(self) -> str:
        #It's the value of text input selected_regex_filter_team_members
        return st.session_state.get(self.SELECTED_REGEX_FILTER_TEAM_MEMBERS_KEY, "")

    def get_selected_status(self) -> List:
        #It's the value of multiselect selected_status
        return st.session_state.get(self.SELECTED_STATUS_KEY, "")

    def get_selected_priority(self) -> List:
        #It's the value of multiselect selected_priority
        return st.session_state.get(self.SELECTED_PRIORITY_KEY, "")

    # Show success
    def get_show_success_todo(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_TODO_KEY, False)

    def set_show_success_todo(self, boolean_success : bool) -> None :
        st.session_state[self.SHOW_SUCCESS_TODO_KEY] = boolean_success

    def get_show_success_project_plan(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_PROJECT_PLAN_KEY, False)

    def set_show_success_project_plan(self, boolean_success : bool) -> None:
        st.session_state[self.SHOW_SUCCESS_PROJECT_PLAN_KEY] = boolean_success

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

    def set_status_change_json(self, list_change_log : List) -> None:
        st.session_state[self.STATUS_CHANGE_JSON_KEY] = list_change_log

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
