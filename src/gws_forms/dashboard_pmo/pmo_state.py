import os
import json
from typing import List
import streamlit as st
import pandas as pd

class PMOState():

    STATUS_CHANGE_LOG_KEY = "status_change_log"
    ACTIVE_PROJECT_PLAN_KEY = "active_project_plan"
    STATUS_CHANGE_JSON_KEY = "status_change_json"
    DF_TO_SAVE_KEY = "df_to_save"
    SHOW_SUCCESS_PROJECT_PLAN_KEY = "show_success_project_plan"
    SHOW_SUCCESS_TODO_KEY = "show_success_todo"

    def __init__(self, df : pd.DataFrame, file_path_change_log : str):
        self.file_path_change_log = file_path_change_log
        # Initialize a log list for status changes
        st.session_state[self.STATUS_CHANGE_LOG_KEY] = self.get_status_change_log()
        st.session_state[self.ACTIVE_PROJECT_PLAN_KEY] = self.get_active_project_plan(df)
        # Initialize a log list for status changes
        st.session_state[self.STATUS_CHANGE_JSON_KEY] = self.get_status_change_json()
        # Initialize a df to save
        st.session_state[self.DF_TO_SAVE_KEY] = df

    # Active project plan
    def active_project_plan(self, df : pd.DataFrame, name_column_active : str) -> pd.DataFrame:
        if self.ACTIVE_PROJECT_PLAN_KEY not in st.session_state or self.get_active_project_plan().empty:
            self.set_active_project_plan(df.copy())
        return st.session_state[self.ACTIVE_PROJECT_PLAN_KEY][st.session_state[self.ACTIVE_PROJECT_PLAN_KEY][name_column_active] == True].copy()

    def set_active_project_plan(self, df: pd.DataFrame) -> None:
        st.session_state[self.ACTIVE_PROJECT_PLAN_KEY] = df

    def get_active_project_plan(self, df : pd.DataFrame = pd.DataFrame()) -> List:
        return st.session_state.get(self.ACTIVE_PROJECT_PLAN_KEY, df.copy())

    # Show success
    def get_show_success_todo(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_TODO_KEY, False)

    def set_show_success_todo(self, boolean_success : bool) -> None :
        st.session_state[self.SHOW_SUCCESS_TODO_KEY] = boolean_success

    def get_show_success_project_plan(self) -> List:
        return st.session_state.get(self.SHOW_SUCCESS_PROJECT_PLAN_KEY, False)

    def set_show_success_project_plan(self, boolean_success : bool) -> None:
        st.session_state[self.SHOW_SUCCESS_PROJECT_PLAN_KEY] = boolean_success

    # Df to save
    def get_df_to_save(self) -> List:
        return st.session_state.get(self.DF_TO_SAVE_KEY)

    def set_df_to_save(self, df: pd.DataFrame) -> None:
        st.session_state[self.DF_TO_SAVE_KEY] = df

    # Status change
    def get_status_change_json(self, nomenclature : str = "list") -> List:
        if nomenclature == "dict":
            nomenclature = {}
        elif nomenclature == "list":
            nomenclature = []
        if self.STATUS_CHANGE_JSON_KEY not in st.session_state or st.session_state[self.STATUS_CHANGE_JSON_KEY] == nomenclature:
            if self.file_path_change_log and os.path.exists(self.file_path_change_log):
                with open(self.file_path_change_log, 'r', encoding="utf-8") as file:
                    st.session_state[self.STATUS_CHANGE_JSON_KEY] = json.load(file)
            else:
                st.session_state[self.STATUS_CHANGE_JSON_KEY] = nomenclature

        return st.session_state.get(self.STATUS_CHANGE_JSON_KEY)


    def set_status_change_json(self, list_change_log : List) -> None:
        st.session_state[self.STATUS_CHANGE_JSON_KEY] = list_change_log

    def get_status_change_log(self) -> List:
        return st.session_state.get(self.STATUS_CHANGE_LOG_KEY, [])

    def convert_log_to_json(self) -> None:
        if self.get_status_change_log():
            if isinstance(self.get_status_change_json(), dict):
                # Ensure `status_change_json` is a list of dictionaries
                if not isinstance(self.get_status_change_json(), list):
                    self.set_status_change_json([self.get_status_change_json()])  # Convert to list

            for new_entry_log in self.get_status_change_log():
                if new_entry_log not in self.get_status_change_json():
                    self.get_status_change_json().append(new_entry_log)
            for entry in self.get_status_change_json():
                if isinstance(entry["status_before"], pd.Series):
                    entry["status_before"] = entry["status_before"].to_string()
            with open(self.file_path_change_log, 'w', encoding="utf-8") as f:
                f.write(json.dumps(self.get_status_change_json(),
                        indent=4, ensure_ascii=False))
