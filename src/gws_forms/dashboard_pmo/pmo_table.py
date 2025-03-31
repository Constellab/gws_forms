import json
import os
from datetime import datetime, timedelta
from typing import Any, Literal, Optional, List
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

#Class to define the different priorities
class Priority(Enum):
    HIGH = "🔴 High"
    MEDIUM = "🟡 Medium"
    LOW = "🟢 Low"

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
    NAME_COLUMN_ACTIVE = "Active"
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
            self.NAME_COLUMN_ACTIVE: self.BOOLEAN,
            self.NAME_COLUMN_UNIQUE_ID: self.TEXT,
            self.NAME_COLUMN_DELETE: self.BOOLEAN
        }
        if self.df is None :
            self.df = pd.DataFrame()
        self.pmo_state = PMOState(self.df, self.file_path_change_log)
        self.df = self.validate_columns(self.df)
        self.df_example = pd.DataFrame({self.NAME_COLUMN_PROJECT_NAME: ["Project 1"],self.NAME_COLUMN_MISSION_NAME: ["Mission 1"],self.NAME_COLUMN_MISSION_REFEREE: ["Person1"],
                            self.NAME_COLUMN_TEAM_MEMBERS: ["Person1, Person2"],self.NAME_COLUMN_START_DATE: "", self.NAME_COLUMN_END_DATE: "",self.NAME_COLUMN_MILESTONES: ["- step 1"],
                            self.NAME_COLUMN_STATUS: [Status.TODO.value],self.NAME_COLUMN_PRIORITY: [Priority.HIGH.value],self.NAME_COLUMN_PROGRESS: [0],
                            self.NAME_COLUMN_COMMENTS: [""],self.NAME_COLUMN_VISIBILITY: [""],self.NAME_COLUMN_ACTIVE: [False],
                            self.NAME_COLUMN_UNIQUE_ID: [StringHelper.generate_uuid()], self.NAME_COLUMN_DELETE : [False]})
        self.edition = True
        self.choice_project_plan = None
        self.original_project_plan_df = None
        #By default, we allow user to add rows to the dataframe Project Plan
        self.dynamic_df = dynamic_df
        self.placeholder_warning_filtering = None
        self.streamlit_data_editor = StreamlitDataEditor()

    # Function to calculate progress
    def calculate_progress(self, row : pd.Series) -> float:
        if row[self.NAME_COLUMN_MILESTONES] == "nan" or pd.isna(row[self.NAME_COLUMN_MILESTONES]):
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

    def track_and_log_status(self, old_df : pd.DataFrame, new_df : pd.DataFrame) -> None:
        """
        Compare old_df and new_df to detect status changes and log them.
        """
        # Keep the current date in ISO format
        current_date = datetime.now().isoformat()

        self.pmo_state.get_status_change_log()

        ### Identify rows where 'status' has changed
        if "level_0" in new_df.columns:
            new_df.set_index("level_0", inplace=True)
        if "index" in new_df.columns:
            new_df.set_index("index", inplace=True)

        # Ensure old_df contains all indices from new_df
        missing_indices = new_df.index.difference(old_df.index)

        # Create a DataFrame with missing indices and copy data from new_df except for STATUS
        if not missing_indices.empty:
            missing_rows = new_df.loc[missing_indices].copy()
            missing_rows[self.NAME_COLUMN_STATUS] = "nan"  # Set STATUS to NaN
            old_df = pd.concat([old_df, missing_rows])  # Append missing rows

        # Remove rows from old_df that are no longer in new_df
        old_df = old_df.loc[old_df.index.intersection(new_df.index)]

        # Now find changed rows
        changed_rows = new_df[new_df[self.NAME_COLUMN_STATUS]
                              != old_df[self.NAME_COLUMN_STATUS]]

        # Load existing log if the file exists
        if self.file_path_change_log:  # Ensure the file path is not None or empty
            try:
                with open(self.file_path_change_log, 'r', encoding="utf-8") as f:
                    existing_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_log = []
        else:
            existing_log = []

        time_tolerance = timedelta(seconds=5)  # Allow 5 seconds of difference

        for idx, row in changed_rows.iterrows():
            old_status = old_df.loc[idx, self.NAME_COLUMN_STATUS]
            new_status = row[self.NAME_COLUMN_STATUS]

            new_entry = {
                "id": row[self.NAME_COLUMN_UNIQUE_ID],
                "project": row[self.NAME_COLUMN_PROJECT_NAME],
                "mission": row[self.NAME_COLUMN_MISSION_NAME],
                "status_before": old_status,
                "status_after": new_status,
                "date": current_date
            }

            # Check if a similar entry already exists within the time tolerance
            if existing_log:
                is_duplicate = any(
                    entry["id"] == new_entry["id"] and
                    entry["project"] == new_entry["project"] and
                    entry["mission"] == new_entry["mission"] and
                    entry["status_before"] == new_entry["status_before"] and
                    entry["status_after"] == new_entry["status_after"] and
                    abs(datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%f") - datetime.strptime(
                        current_date, "%Y-%m-%dT%H:%M:%S.%f")) <= time_tolerance
                    for entry in existing_log
                )
            else:
                is_duplicate = False
            if not is_duplicate:
                self.pmo_state.get_status_change_log().append(new_entry)

        # Convert the log to JSON
        self.pmo_state.convert_log_to_json()

    def fill_na_df(self, df : pd.DataFrame) -> pd.DataFrame:
        for column, col_type in self.required_columns.items():
            if column not in df.columns:
                df[column] = None
            if col_type == self.DATE:
                df[column] = df[column].fillna('').astype('datetime64[ns]')
            elif col_type == self.TEXT:
                df[column] = df[column].astype(str)
            elif col_type == self.NUMERIC:
                df[column] = df[column].astype(float)
            elif col_type == self.BOOLEAN:
                df[column] = df[column].astype(bool)

        # Replace empty strings with No members in the Team members column in order to show it in the Gantt chart
        df[self.NAME_COLUMN_TEAM_MEMBERS] = df[self.NAME_COLUMN_TEAM_MEMBERS].replace([
                                                                                      '', 'None', 'nan'], 'No members')
        # Replace empty text columns by 'nan'
        df[self.NAME_COLUMN_PROJECT_NAME] = df[self.NAME_COLUMN_PROJECT_NAME].replace([
                                                                                      '', 'None'], 'nan')
        df[self.NAME_COLUMN_MISSION_NAME] = df[self.NAME_COLUMN_MISSION_NAME].replace([
                                                                                      '', 'None'], 'nan')
        df[self.NAME_COLUMN_MISSION_REFEREE] = df[self.NAME_COLUMN_MISSION_REFEREE].replace([
                                                                                            '', 'None'], 'nan')
        df[self.NAME_COLUMN_MILESTONES] = df[self.NAME_COLUMN_MILESTONES].replace([
                                                                                  '', 'None'], 'nan')
        df[self.NAME_COLUMN_STATUS] = df[self.NAME_COLUMN_STATUS].replace([
                                                                          '', 'None'], 'nan')
        df[self.NAME_COLUMN_PRIORITY] = df[self.NAME_COLUMN_PRIORITY].replace([
                                                                              '', 'None'], 'nan')
        df[self.NAME_COLUMN_COMMENTS] = df[self.NAME_COLUMN_COMMENTS].replace([
                                                                              '', 'None'], 'nan')
        df[self.NAME_COLUMN_VISIBILITY] = df[self.NAME_COLUMN_VISIBILITY].replace([
                                                                                  '', 'None'], 'nan')
        df[self.NAME_COLUMN_UNIQUE_ID] = df[self.NAME_COLUMN_UNIQUE_ID].replace([
                                                                                '', 'None'], 'nan')
        # Set active and delete to False if empty
        df[self.NAME_COLUMN_ACTIVE] = df[self.NAME_COLUMN_ACTIVE].replace(
            '', False)
        df[self.NAME_COLUMN_DELETE] = df[self.NAME_COLUMN_DELETE].replace(
            '', False)
        # Convert None to pd.NaT
        df[self.NAME_COLUMN_START_DATE] = df[self.NAME_COLUMN_START_DATE].apply(
            lambda x: pd.NaT if x is None else x)
        df[self.NAME_COLUMN_END_DATE] = df[self.NAME_COLUMN_END_DATE].apply(
            lambda x: pd.NaT if x is None else x)

        # Add a unique id to each line if not set yet
        df[self.NAME_COLUMN_UNIQUE_ID] = df[self.NAME_COLUMN_UNIQUE_ID].apply(
            lambda x: StringHelper.generate_uuid() if x == "nan" else x)
        return df

    def validate_columns(self, df : pd.DataFrame) -> pd.DataFrame:
        """Ensures the required columns are present and have the correct types."""
        df = self.fill_na_df(df)

        # If status is Done and there is no end date, then set current date to the column end date
        for idx, row in df.iterrows():
            if row[self.NAME_COLUMN_STATUS] == Status.DONE.value and pd.isna(row[self.NAME_COLUMN_END_DATE]):
                # Set end date
                end_date = datetime.now(tz=pytz.timezone(
                    'Europe/Paris')).strftime("%d %m %Y")
                df.at[idx, self.NAME_COLUMN_END_DATE] = end_date

        # Apply the function to calculate progress
        df[self.NAME_COLUMN_PROGRESS] = df.apply(
            self.calculate_progress, axis=1)

        # Track the changes of status
        # Keep the current date at iso format
        current_date = datetime.now().isoformat()

        self.pmo_state.get_status_change_log()

        # Load existing log if the file exists
        if self.file_path_change_log:  # Ensure the file path is not None or empty
            try:
                with open(self.file_path_change_log, 'r', encoding="utf-8") as f:
                    existing_log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_log = []
        else:
            existing_log = []

        time_tolerance = timedelta(seconds=5)  # Allow 5 seconds of difference

        # Change status to '✅ Done' if progress is 100 + set today’s date in 'End Date'
        for idx, row in df.iterrows():
            if (
                row[self.NAME_COLUMN_PROGRESS] == 100 and
                row[self.NAME_COLUMN_STATUS] in [Status.IN_PROGRESS.value, Status.TODO.value]
            ):
                old_status = row[self.NAME_COLUMN_STATUS]
                new_status = Status.DONE.value
                df.loc[idx, self.NAME_COLUMN_STATUS] = new_status
                if pd.isna(row[self.NAME_COLUMN_END_DATE]):
                    df.loc[idx, self.NAME_COLUMN_END_DATE] = datetime.now(
                        tz=pytz.timezone('Europe/Paris')).strftime("%d %m %Y")  # Set end date

                # Log the change
                new_entry = {
                    "id": row[self.NAME_COLUMN_UNIQUE_ID],
                    "project": row[self.NAME_COLUMN_PROJECT_NAME],
                    "mission": row[self.NAME_COLUMN_MISSION_NAME],
                    "status_before": old_status,
                    "status_after": new_status,
                    "date": current_date
                }

                # Check if a similar entry already exists within the time tolerance
                if existing_log:
                    is_duplicate = any(
                        entry["id"] == new_entry["id"] and
                        entry["project"] == new_entry["project"] and
                        entry["mission"] == new_entry["mission"] and
                        entry["status_before"] == new_entry["status_before"] and
                        entry["status_after"] == new_entry["status_after"] and
                        abs(datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%f") - datetime.strptime(
                            current_date, "%Y-%m-%dT%H:%M:%S.%f")) <= time_tolerance
                        for entry in existing_log
                    )
                else:
                    is_duplicate = False

                if not is_duplicate:
                    self.pmo_state.get_status_change_log().append(new_entry)

        # Iterate through each mission

        if self.missions_order:
            # Exclude the last mission
            for idx, mission in enumerate(self.missions_order[:-1]):
                # Adjust the column name if necessary
                current_mission_mask = df[self.NAME_COLUMN_MISSION_NAME] == mission
                next_mission = self.missions_order[idx + 1]
                next_mission_mask = df[self.NAME_COLUMN_MISSION_NAME] == next_mission

                # Get unique project names for the current mission
                current_project_names = df.loc[current_mission_mask & (
                    df[self.NAME_COLUMN_STATUS] == Status.DONE.value), self.NAME_COLUMN_PROJECT_NAME].unique()
                # Update the next mission only if the project name matches
                for project_name in current_project_names:
                    project_mask = df[self.NAME_COLUMN_PROJECT_NAME] == project_name
                    # Update start date and status for the next mission
                    for next_idx, next_row in df[next_mission_mask & project_mask].iterrows():
                        if pd.isna(next_row[self.NAME_COLUMN_START_DATE]):
                            df.loc[next_idx, self.NAME_COLUMN_START_DATE] = datetime.now(
                                tz=pytz.timezone('Europe/Paris')).strftime("%d %m %Y")
                        if next_row[self.NAME_COLUMN_STATUS] == Status.TODO.value:
                            old_status = next_row[self.NAME_COLUMN_STATUS]
                            new_status = Status.IN_PROGRESS.value
                            df.loc[next_idx, self.NAME_COLUMN_STATUS] = new_status

                            # Log the change
                            new_entry = {
                                "id": next_row[self.NAME_COLUMN_UNIQUE_ID],
                                "project": next_row[self.NAME_COLUMN_PROJECT_NAME],
                                "mission": next_row[self.NAME_COLUMN_MISSION_NAME],
                                "status_before": old_status,
                                "status_after": new_status,
                                "date": current_date
                            }

                            # Check if a similar entry already exists within the time tolerance
                            if existing_log:
                                is_duplicate = any(
                                    entry["id"] == new_entry["id"] and
                                    entry["project"] == new_entry["project"] and
                                    entry["mission"] == new_entry["mission"] and
                                    entry["status_before"] == new_entry["status_before"] and
                                    entry["status_after"] == new_entry["status_after"] and
                                    abs(datetime.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S.%f") - datetime.strptime(
                                        current_date, "%Y-%m-%dT%H:%M:%S.%f")) <= time_tolerance
                                    for entry in existing_log
                                )
                            else:
                                is_duplicate = False

                            if not is_duplicate:
                                self.pmo_state.get_status_change_log().append(new_entry)

        # Convert the log to JSON
        if self.pmo_state.get_status_change_log():
            self.pmo_state.convert_log_to_json()

            # Filter rows in order to show "In progress", "Todo" before "Done" and "Closed" -> for a better use
            # group by project name
            # Define the custom order for the "status" column
            status_order = {Status.IN_PROGRESS.value: 0,
                            Status.TODO.value: 1, Status.DONE.value: 2, Status.CLOSED.value: 3}

            # Create a temporary column for the sort order based on "status"
            df["status_order"] = df[self.NAME_COLUMN_STATUS].map(status_order)

            # Sort the DataFrame
            df = (
                df.sort_values(by=[self.NAME_COLUMN_PROJECT_NAME, "status_order"])
                # Group by project_name
                .groupby(self.NAME_COLUMN_PROJECT_NAME, group_keys=False)
                # Sort within each group
                .apply(lambda group: group.sort_values("status_order"))
            )

            # Drop the temporary column if no longer needed
            df = df.drop(columns=["status_order"])

            # Reset index
            df = df.reset_index(drop=True)

        return df

    def calculate_height(self) -> int:
        # Define the height of the dataframe : self.ROWS_TO_SHOW rows to show or the number of max rows
        active_plan = self.pmo_state.active_project_plan(self.df, self.NAME_COLUMN_ACTIVE)
        if len(active_plan) < self.ROWS_TO_SHOW :
            return self.ROW_HEIGHT*(len(active_plan)+1) + self.HEADER_HEIGHT
        else:
            return self.HEADER_HEIGHT + self.ROW_HEIGHT * self.ROWS_TO_SHOW

    def get_index(self, row : pd.Series) -> int:
        return self.pmo_state.active_project_plan(self.df, self.NAME_COLUMN_ACTIVE).iloc[row].name

    def commit(self) -> None:
        # Apply edits, additions, and deletions
        dataframe_to_modify = self.streamlit_data_editor.process_changes(dataframe_to_modify = self.pmo_state.get_active_project_plan(),
                                                                        dataframe_displayed = self.pmo_state.active_project_plan(self.df, self.NAME_COLUMN_ACTIVE),
                                                                        handle_deleted_rows = True,
                                                                        column_deleted=self.NAME_COLUMN_DELETE)
        # Check if deleted_rows is not empty
        if self.streamlit_data_editor.get_deleted_rows():
            self.pmo_state.set_active_project_plan(dataframe_to_modify)
