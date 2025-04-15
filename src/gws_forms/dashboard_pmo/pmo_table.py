import json
import os
from datetime import datetime, timedelta
from typing import Any, Literal, Optional, List, Dict
from abc import abstractmethod
from enum import Enum
import pytz
import pandas as pd
from gws_forms.e_table.e_table import Etable
from gws_forms.dashboard_pmo.pmo_state import PMOState
from gws_forms.dashboard_pmo.streamlit_data_editor import StreamlitDataEditor
from gws_core import StringHelper

# Code inspired by this tutorial : https://medium.com/codex/create-a-simple-project-planning-app-using-streamlit-and-gantt-chart-6c6adf8f46dd

class Event:
    def __init__(self, event_type: Literal['create_line', 'delete_line', 'update_line'], data: Any = None):
        self.event_type = event_type # Store the event type
        self.data = data

class MessageObserver:
    @abstractmethod
    def update(self, event: Event) -> bool:
        """Method called when a message is dispatched"""
        #This method is implemented in subclasses to update tags on folders when the project plan is saved
        pass

#Class to define the different status
class Status(Enum):
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
        }
        return order

#Class to define the different priorities
class Priority(Enum):
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
            cls.LOW.value: "#59d95e"
        }
        return colors

class PMOTable(Etable):

    # Define columns names
    NAME_COLUMN_START_DATE = 'Start Date'
    NAME_COLUMN_END_DATE = 'End Date'
    NAME_COLUMN_MILESTONES = 'Milestones'
    NAME_COLUMN_PRIORITY = 'Priority'
    NAME_COLUMN_PROGRESS = 'Progress (%)'
    NAME_COLUMN_COMMENTS = 'Comments'
    NAME_COLUMN_VISIBILITY = 'Visibility'
    NAME_COLUMN_PROJECT_NAME = 'Project Name'
    NAME_COLUMN_MISSION_NAME = 'Mission Name'
    NAME_COLUMN_MISSION_REFEREE = 'Mission Referee'
    NAME_COLUMN_TEAM_MEMBERS = 'Team Members'
    NAME_COLUMN_STATUS = "Status"
    NAME_COLUMN_UNIQUE_ID = "ID"
    NAME_COLUMN_DELETE = "Delete"
    DEFAULT_COLUMNS_LIST = [NAME_COLUMN_PROJECT_NAME, NAME_COLUMN_MISSION_NAME, NAME_COLUMN_MISSION_REFEREE, NAME_COLUMN_TEAM_MEMBERS, NAME_COLUMN_START_DATE,
                            NAME_COLUMN_END_DATE, NAME_COLUMN_MILESTONES, NAME_COLUMN_STATUS, NAME_COLUMN_PRIORITY, NAME_COLUMN_PROGRESS, NAME_COLUMN_COMMENTS,
                            NAME_COLUMN_VISIBILITY, NAME_COLUMN_DELETE]
    # Constants for height calculation
    ROW_HEIGHT = 35  # Height per row in pixels
    HEADER_HEIGHT = 38  # Height for the header in pixels
    ROWS_TO_SHOW = 11 # 11 rows is the number of rows in plain page for basic screen

    json_path : str
    folder_project_plan : str
    folder_details : str
    missions_order : List
    folder_change_log : str
    dynamic_df : str
    observer : Optional[MessageObserver]

    def __init__(self, json_path = None, folder_project_plan = None, folder_details = None, missions_order = None, folder_change_log = None, dynamic_df = "dynamic", observer = None):
        """
        Initialize the PMOTable object with the data file containing the project missions.
        Functions will define the actions to perform with the PMO table in order to see them in the dashboard
        """
        super().__init__(json_path)
        if missions_order is None:
            self.missions_order = []
        else:
            self.missions_order = missions_order
        self.observer = observer
        self.folder_project_plan = folder_project_plan
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
        self.required_columns = {
            self.NAME_COLUMN_PROJECT_NAME: self.TEXT,
            self.NAME_COLUMN_MISSION_NAME: self.TEXT,
            self.NAME_COLUMN_MISSION_REFEREE: self.TEXT,
            self.NAME_COLUMN_TEAM_MEMBERS: self.TEXT,
            self.NAME_COLUMN_START_DATE: self.DATE,
            self.NAME_COLUMN_END_DATE: self.DATE,
            self.NAME_COLUMN_MILESTONES: self.TEXT,
            self.NAME_COLUMN_STATUS: self.TEXT,
            self.NAME_COLUMN_PRIORITY: self.TEXT,
            self.NAME_COLUMN_PROGRESS: self.NUMERIC,
            self.NAME_COLUMN_COMMENTS: self.TEXT,
            self.NAME_COLUMN_VISIBILITY: self.TEXT,
            self.NAME_COLUMN_UNIQUE_ID: self.TEXT,
            self.NAME_COLUMN_DELETE: self.BOOLEAN
        }
        self.df = pd.DataFrame()
        self.pmo_state = PMOState(self.file_path_change_log)
        self.validate_columns()
        self.df_example = pd.DataFrame({self.NAME_COLUMN_PROJECT_NAME: ["Project 1"],
                                        self.NAME_COLUMN_MISSION_NAME: ["Mission 1"],self.NAME_COLUMN_MISSION_REFEREE: ["Person1"],
                                        self.NAME_COLUMN_TEAM_MEMBERS: ["Person1, Person2"],
                                        self.NAME_COLUMN_START_DATE: datetime.now(tz=pytz.timezone('Europe/Paris')).strftime("%d %m %Y"),
                                        self.NAME_COLUMN_END_DATE: "",self.NAME_COLUMN_MILESTONES: ["- step 1"],
                                        self.NAME_COLUMN_STATUS: [Status.TODO.value],self.NAME_COLUMN_PRIORITY: [Priority.HIGH.value],self.NAME_COLUMN_PROGRESS: [0],
                                        self.NAME_COLUMN_COMMENTS: ["/"],self.NAME_COLUMN_VISIBILITY: ["/"],
                                        self.NAME_COLUMN_UNIQUE_ID: [StringHelper.generate_uuid()], self.NAME_COLUMN_DELETE : [False]})
        self.choice_project_plan = None
        #By default, we allow user to add rows to the dataframe Project Plan
        self.dynamic_df = dynamic_df
        self.placeholder_warning_filtering = None
        self.table_editing_state = False


    def get_filter_df(self, only_closed_status : bool = False) -> pd.DataFrame:
        """
        Filters the main DataFrame based on user-selected filters.

        If 'only_closed_status' is 'True', the function applies all selected filters except for status,
        where only rows with the status "Closed" are retained. This is used in the closed project tab
        to ensure only closed projects are displayed.
        """

        # Ensure the date columns are in datetime format
        self.df[self.NAME_COLUMN_START_DATE] = pd.to_datetime(self.df[self.NAME_COLUMN_START_DATE], errors='coerce').dt.date
        self.df[self.NAME_COLUMN_END_DATE] = pd.to_datetime(self.df[self.NAME_COLUMN_END_DATE], errors='coerce').dt.date
        partial_df = self.df.copy()
        #Retrieve the values of filters
        selected_regex_filter_project_name = self.pmo_state.get_selected_regex_filter_project_name()
        selected_regex_filter_mission_name = self.pmo_state.get_selected_regex_filter_mission_name()
        selected_mission_referee = self.pmo_state.get_selected_mission_referee()
        selected_regex_filter_team_members = self.pmo_state.get_selected_regex_filter_team_members()
        selected_status = self.pmo_state.get_selected_status()
        selected_priority = self.pmo_state.get_selected_priority()

        # Initialize the filter condition to True (for all rows)
        filter_condition = pd.Series(True, index=self.df.index)

        if selected_regex_filter_project_name:
            filter_condition &= self.df[PMOTable.NAME_COLUMN_PROJECT_NAME].str.contains(selected_regex_filter_project_name, case=False)
        if selected_regex_filter_mission_name:
            filter_condition &= self.df[PMOTable.NAME_COLUMN_MISSION_NAME].str.contains(selected_regex_filter_mission_name, case=False)
        if selected_mission_referee:
            filter_condition &= self.df[PMOTable.NAME_COLUMN_MISSION_REFEREE].isin(selected_mission_referee)
        if selected_regex_filter_team_members:
            filter_condition &= self.df[PMOTable.NAME_COLUMN_TEAM_MEMBERS].str.contains(selected_regex_filter_team_members, case=False)
        # Apply status filtering conditionally
        if only_closed_status:
            filter_condition &= self.df[PMOTable.NAME_COLUMN_STATUS] == Status.CLOSED.value
        elif selected_status:
            filter_condition &= self.df[PMOTable.NAME_COLUMN_STATUS].isin(selected_status)

        if selected_priority:
            filter_condition &=self.df[PMOTable.NAME_COLUMN_PRIORITY].isin(selected_priority)

        # Filter the DataFrame using the filter_condition
        partial_df = partial_df[filter_condition]

        return partial_df


    # Function to calculate progress
    def calculate_progress(self, row : pd.Series) -> float:
        if pd.isna(row[self.NAME_COLUMN_MILESTONES]) or row[self.NAME_COLUMN_MILESTONES] == "nan":
            return 0
        # Count the number of steps (total "-"" and "✅")
        total_steps = row[self.NAME_COLUMN_MILESTONES].count(
            "-") + row[self.NAME_COLUMN_MILESTONES].count("✅")
        # Count the number of completed steps (✅ only)
        completed_steps = row[self.NAME_COLUMN_MILESTONES].count("✅")
        # Calculate the progress as a percentage
        if total_steps > 0:
            return (completed_steps / total_steps) * 100
        else:
            return 0

    def track_and_log_status(self, new_df : pd.DataFrame) -> None:
        """
        Compare old_df (self.df) and new_df to detect status changes and log them.
        """
        old_df = self.df.copy()
        new_df = new_df.copy()
        # Keep the current date in ISO format
        current_date = datetime.now().isoformat()
        self.pmo_state.get_status_change_log()
        time_tolerance = timedelta(seconds=5) # Allow 5 seconds of difference

        ### Identify rows where 'status' has changed
        if "level_0" in new_df.columns:
            new_df.set_index("level_0", inplace=True)
        if "index" in new_df.columns:
            new_df.set_index("index", inplace=True)

        # Ensure old_df (self.df) contains all indices from new_df
        missing_indices = new_df.index.difference(old_df.index)
        # Create a DataFrame with missing indices and copy data from new_df except for STATUS
        if not missing_indices.empty:
            missing_rows = new_df.loc[missing_indices].copy()
            missing_rows[self.NAME_COLUMN_STATUS] = "nan"  # Set STATUS to NaN
            old_df = pd.concat([old_df, missing_rows])  # Append missing rows

        # Remove rows from old_df (self.df) that are no longer in new_df
        old_df = old_df.loc[old_df.index.intersection(new_df.index)]
        # Load existing log file
        existing_log = self._load_existing_log()
        # Now find changed rows
        changed_rows = new_df[new_df[self.NAME_COLUMN_STATUS] != old_df[self.NAME_COLUMN_STATUS]]

        for idx, row in changed_rows.iterrows():
            old_status = old_df.loc[idx, self.NAME_COLUMN_STATUS]
            new_status = row[self.NAME_COLUMN_STATUS]

            new_entry = self._create_log_entry(row, old_status, new_status, current_date)

            if not self._is_duplicate_entry(new_entry, existing_log, time_tolerance):
                self.pmo_state.append_status_change_log(new_entry)
        # Convert the log to JSON
        self.pmo_state.convert_log_to_json()

    def _load_existing_log(self):
        if self.file_path_change_log:
            try:
                with open(self.file_path_change_log, 'r', encoding="utf-8") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return []
        return []

    def _create_log_entry(self, row, old_status, new_status, date_str):
        return {
            "id": row[self.NAME_COLUMN_UNIQUE_ID],
            "project": row[self.NAME_COLUMN_PROJECT_NAME],
            "mission": row[self.NAME_COLUMN_MISSION_NAME],
            "status_before": old_status,
            "status_after": new_status,
            "date": date_str
        }

    def _is_duplicate_entry(self, entry, log, tolerance):
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%f")
        return any(
            entry["id"] == entry["id"] and
            entry["project"] == entry["project"] and
            entry["mission"] == entry["mission"] and
            entry["status_before"] == entry["status_before"] and
            entry["status_after"] == entry["status_after"] and
            abs(datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%f") - entry_date) <= tolerance
            for entry in log
        )

    def fill_na_df(self) -> None:
        for column, col_type in self.required_columns.items():
            if column not in self.df.columns:
                self.df[column] = None
            if col_type == self.DATE:
                self.df[column] = self.df[column].fillna('').astype('datetime64[ns]')
            elif col_type == self.TEXT:
                self.df[column] = self.df[column].astype("string")
            elif col_type == self.NUMERIC:
                self.df[column] = self.df[column].astype(float)
            elif col_type == self.BOOLEAN:
                self.df[column] = self.df[column].astype(bool)

        # Replace empty strings with No members in the Team members column in order to show it in the Gantt chart
        self.df[self.NAME_COLUMN_TEAM_MEMBERS] = self.df[self.NAME_COLUMN_TEAM_MEMBERS].replace([
                                                                                      '', 'None', 'nan'], 'No members')
        # Replace empty text columns by 'nan'
        self.df[self.NAME_COLUMN_PROJECT_NAME] = self.df[self.NAME_COLUMN_PROJECT_NAME].replace([
                                                                                      '', 'None'], '/')
        self.df[self.NAME_COLUMN_MISSION_NAME] = self.df[self.NAME_COLUMN_MISSION_NAME].replace([
                                                                                      '', 'None'], '/')
        self.df[self.NAME_COLUMN_MISSION_REFEREE] = self.df[self.NAME_COLUMN_MISSION_REFEREE].replace([
                                                                                            '', 'None'], '/')
        self.df[self.NAME_COLUMN_MILESTONES] = self.df[self.NAME_COLUMN_MILESTONES].replace([
                                                                                  '', 'None'], '/')
        self.df[self.NAME_COLUMN_STATUS] = self.df[self.NAME_COLUMN_STATUS].replace([
                                                                          '', 'None'], 'nan')
        self.df[self.NAME_COLUMN_PRIORITY] = self.df[self.NAME_COLUMN_PRIORITY].replace([
                                                                              '', 'None'], 'nan')
        self.df[self.NAME_COLUMN_COMMENTS] = self.df[self.NAME_COLUMN_COMMENTS].replace([
                                                                              '', 'None'], "/")
        self.df[self.NAME_COLUMN_VISIBILITY] = self.df[self.NAME_COLUMN_VISIBILITY].replace([
                                                                                  '', 'None'], "/")
        self.df[self.NAME_COLUMN_UNIQUE_ID] = self.df[self.NAME_COLUMN_UNIQUE_ID].replace([
                                                                                '', 'None'], '/')
        # Set delete to False if empty
        self.df[self.NAME_COLUMN_DELETE] = self.df[self.NAME_COLUMN_DELETE].replace(
            '', False)
        # Convert None to pd.NaT
        self.df[self.NAME_COLUMN_START_DATE] = self.df[self.NAME_COLUMN_START_DATE].apply(
            lambda x: pd.NaT if x is None else x)
        self.df[self.NAME_COLUMN_END_DATE] = self.df[self.NAME_COLUMN_END_DATE].apply(
            lambda x: pd.NaT if x is None else x)
        # Ensure the date columns are in datetime format
        self.df[self.NAME_COLUMN_START_DATE] = pd.to_datetime(self.df[self.NAME_COLUMN_START_DATE], errors='coerce').dt.date
        self.df[self.NAME_COLUMN_END_DATE] = pd.to_datetime(self.df[self.NAME_COLUMN_END_DATE], errors='coerce').dt.date

        # Add a unique id to each line if not set yet
        self.df[self.NAME_COLUMN_UNIQUE_ID] = self.df[self.NAME_COLUMN_UNIQUE_ID].apply(
            lambda x: StringHelper.generate_uuid() if pd.isna(x) or x == "/" else x)

    def validate_columns(self) -> None:
        """Ensures the required columns are present and have the correct types
        and auto-update based on progress."""
        self.fill_na_df()
        # Keep the current date at iso format
        current_date = datetime.now().isoformat()
        current_date_str = datetime.now(pytz.timezone('Europe/Paris')).strftime("%d %m %Y")
        time_tolerance = timedelta(seconds=5)


        # If status is Done and there is no end date, then set current date to the column end date
        for idx, row in self.df.iterrows():
            if (not pd.isna(row[self.NAME_COLUMN_STATUS])
                and row[self.NAME_COLUMN_STATUS] == Status.DONE.value
                and pd.isna(row[self.NAME_COLUMN_END_DATE])
            ):
                # Auto set end date for DONE status
                self.df.at[idx, self.NAME_COLUMN_END_DATE] = current_date_str

        # Apply the function to calculate progress
        self.df[self.NAME_COLUMN_PROGRESS] = self.df.apply(
            self.calculate_progress, axis=1)

        # Track the changes of status
        self.pmo_state.get_status_change_log()

        existing_log = self._load_existing_log()

        # Change status to '✅ Done' if progress is 100 + set today’s date in 'End Date'
        for idx, row in self.df.iterrows():
            if (
                row[self.NAME_COLUMN_PROGRESS] == 100 and
                row[self.NAME_COLUMN_STATUS] in [Status.IN_PROGRESS.value, Status.TODO.value]
            ):
                old_status = row[self.NAME_COLUMN_STATUS]
                new_status = Status.DONE.value
                self.df.loc[idx, self.NAME_COLUMN_STATUS] = new_status
                if pd.isna(row[self.NAME_COLUMN_END_DATE]):
                    self.df.loc[idx, self.NAME_COLUMN_END_DATE] = current_date_str

                new_entry = self._create_log_entry(row, old_status, new_status, current_date)
                # Check if a similar entry already exists within the time tolerance
                if not self._is_duplicate_entry(new_entry, existing_log, time_tolerance):
                    self.pmo_state.append_status_change_log(new_entry)

        # Iterate through each mission
        if self.missions_order:
            # Exclude the last mission
            for idx, mission in enumerate(self.missions_order[:-1]):
                # Adjust the column name if necessary
                current_mission_mask = self.df[self.NAME_COLUMN_MISSION_NAME] == mission
                next_mission = self.missions_order[idx + 1]
                next_mission_mask = self.df[self.NAME_COLUMN_MISSION_NAME] == next_mission

                # Get unique project names for the current mission
                current_project_names = self.df.loc[current_mission_mask & (
                    self.df[self.NAME_COLUMN_STATUS] == Status.DONE.value), self.NAME_COLUMN_PROJECT_NAME].unique()
                # Update the next mission only if the project name matches
                for project_name in current_project_names:
                    project_mask = self.df[self.NAME_COLUMN_PROJECT_NAME] == project_name
                    # Update start date and status for the next mission
                    for next_idx, next_row in self.df[next_mission_mask & project_mask].iterrows():
                        if pd.isna(next_row[self.NAME_COLUMN_START_DATE]):
                            self.df.loc[next_idx, self.NAME_COLUMN_START_DATE] = datetime.now(
                                tz=pytz.timezone('Europe/Paris')).strftime("%d %m %Y")
                        if next_row[self.NAME_COLUMN_STATUS] == Status.TODO.value:
                            old_status = next_row[self.NAME_COLUMN_STATUS]
                            new_status = Status.IN_PROGRESS.value
                            self.df.loc[next_idx, self.NAME_COLUMN_STATUS] = new_status

                            new_entry = self._create_log_entry(next_row, old_status, new_status, current_date)
                            if not self._is_duplicate_entry(new_entry, existing_log, time_tolerance):
                                self.pmo_state.append_status_change_log(new_entry)

        # Convert the log to JSON
        if self.pmo_state.get_status_change_log():
            self.pmo_state.convert_log_to_json()

        # Filter rows in order to show "In progress", "Todo" before "Done" and "Closed" -> for a better use
        # group by project name
        # Define the categorical order for sorting
        status_order = Status.get_order()

        # Sort the DataFrame
        self.df = self.df.sort_values(
            by=[self.NAME_COLUMN_PROJECT_NAME, self.NAME_COLUMN_STATUS],
            key=lambda col: col.map(status_order) if col.name == self.NAME_COLUMN_STATUS else col
            )

        # Reset index
        self.df = self.df.reset_index(drop=True)

    def calculate_height(self) -> int:
        # Define the height of the dataframe : self.ROWS_TO_SHOW rows to show or the number of max rows
        active_plan = self.get_filter_df()
        if len(active_plan) < self.ROWS_TO_SHOW :
            return self.ROW_HEIGHT*(len(active_plan)+1) + self.HEADER_HEIGHT
        else:
            return self.HEADER_HEIGHT + self.ROW_HEIGHT * self.ROWS_TO_SHOW

    def commit(self, streamlit_data_editor : StreamlitDataEditor) -> None:
        # Add a unique id to each line if not set yet
        streamlit_data_editor.dataframe_displayed[self.NAME_COLUMN_UNIQUE_ID] = streamlit_data_editor.dataframe_displayed[self.NAME_COLUMN_UNIQUE_ID].apply(
            lambda x: StringHelper.generate_uuid() if pd.isna(x) or x == "/" else x)

        self.track_and_log_status(new_df=streamlit_data_editor.dataframe_displayed)
        # Apply edits, additions, and deletions
        self.df = streamlit_data_editor.process_changes(dataframe_to_modify = self.df,
                                                        column_unique_id= self.NAME_COLUMN_UNIQUE_ID,
                                                        handle_deleted_rows = True,
                                                        column_deleted=self.NAME_COLUMN_DELETE)
        self.validate_columns()

    def save_df_in_folder(self) -> None:
        # Save dataframe in the folder
        timestamp = datetime.now(tz=pytz.timezone(
            'Europe/Paris')).strftime("plan_%Y-%m-%d-%Hh%M")
        path_csv = os.path.join(
            self.folder_project_plan, f"{timestamp}.csv")
        self.df.to_csv(path_csv, index=False)
