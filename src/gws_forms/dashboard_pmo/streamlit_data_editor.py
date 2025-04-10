from typing import Dict, Any, List
import pandas as pd
import streamlit as st


class StreamlitDataEditor():
    """
    This class uses the session state of the st.data_editor from Streamlit.
    It provides functions to work with this component.
    """

    EDITOR_KEY = "editor"
    EDITED_ROWS_KEY = "edited_rows"
    ADDED_ROWS_KEY = "added_rows"
    DELETED_ROWS_KEY = "deleted_rows"

    def __init__(self):
        a = None
        """if self.EDITOR_KEY not in st.session_state:
            st.session_state.editor = {
                self.EDITED_ROWS_KEY: {},
                self.ADDED_ROWS_KEY: [],
                self.DELETED_ROWS_KEY: []
            }"""

    def get_edited_rows(self) -> Dict[int, Dict[str, Any]]:
        return st.session_state[self.EDITOR_KEY].get(self.EDITED_ROWS_KEY, {})

    def get_added_rows(self) -> List[Dict[str, Any]]:
        return st.session_state[self.EDITOR_KEY].get(self.ADDED_ROWS_KEY, [])

    def get_deleted_rows(self) -> List[int]:
        return st.session_state[self.EDITOR_KEY].get(self.DELETED_ROWS_KEY, [])

    def append_deleted_rows(self, value) -> None:
        st.session_state[self.EDITOR_KEY][self.DELETED_ROWS_KEY].append(value)

    def get_index(self, row : pd.Series, dataframe_displayed : pd.DataFrame) -> int:
        return dataframe_displayed.iloc[row].name


    def apply_edited_rows(self, dataframe_to_modify : pd.DataFrame, dataframe_displayed: pd.DataFrame) -> pd.DataFrame:
        """
        Apply user edits from the displayed DataFrame to the original DataFrame.

        This function updates `dataframe_to_modify` by applying changes made in `dataframe_displayed`.
        It ensures that all modified values are transferred to the original DataFrame while preserving
        the overall structure.

        Parameters:
            dataframe_to_modify (pd.DataFrame): The original DataFrame to be updated with user edits.
            dataframe_displayed (pd.DataFrame): The DataFrame reflecting user modifications.

        Returns:
            pd.DataFrame: The updated DataFrame with applied edits.
        """

        # Apply edited rows
        if self.get_edited_rows():
            for row in self.get_edited_rows():
                row_index = self.get_index(row, dataframe_displayed)
                for key, value in self.get_edited_rows()[row].items():
                    dataframe_to_modify.at[row_index, key] = value
        return dataframe_to_modify

    def apply_edited_rows_and_handle_deleted_rows(self, dataframe_to_modify: pd.DataFrame, dataframe_displayed: pd.DataFrame, column_deleted : str) -> pd.DataFrame:
        """
        Apply edits from the displayed DataFrame to the original DataFrame and handle row deletions.

        This function updates `dataframe_to_modify` with the changes made in `dataframe_displayed`.
        Additionally, if a specified column (e.g., "deleted") is provided and contains checkbox values (True/False),
        rows where the value is True will be marked for deletion.

        Parameters:
            dataframe_to_modify (pd.DataFrame): The original DataFrame to be updated.
            dataframe_displayed (pd.DataFrame): The DataFrame containing user edits.
            column_deleted (str): The name of the column used to mark rows for deletion.
                                This column must contain boolean values (True/False).

        Returns:
            pd.DataFrame: The modified DataFrame with applied edits. Rows marked for deletion
                        are handled separately but not removed within this function.
        """
        # Apply edited rows
        if self.get_edited_rows():
            for row in self.get_edited_rows():
                row_index = self.get_index(row, dataframe_displayed)

                for key, value in self.get_edited_rows()[row].items():
                    dataframe_to_modify.at[row_index, key] = value

                    # If the "delete" column is set to True, add the index to deleted_rows
                    if key == column_deleted and value is True:
                        self.append_deleted_rows(int(row))  # Ensure row is stored as an integer

        return dataframe_to_modify

    def apply_added_rows(self, dataframe_to_modify : pd.DataFrame) -> pd.DataFrame:
        """
        Apply newly added rows to the given DataFrame.

        This function integrates new rows into `dataframe_to_modify` based on user inputs
        or modifications made within the application.

        Parameters:
            dataframe_to_modify (pd.DataFrame): The DataFrame to which new rows will be added.

        Returns:
            pd.DataFrame: The updated DataFrame including the newly added rows.
        """
        # Apply added rows
        if self.get_added_rows():
            for row in self.get_added_rows():
                row_index = len(dataframe_to_modify)
                for key, value in row.items():
                    dataframe_to_modify.at[row_index, key] = value
        return dataframe_to_modify

    def apply_deleted_rows(self, dataframe_to_modify : pd.DataFrame, dataframe_displayed: pd.DataFrame)-> pd.DataFrame:
        """
        Remove rows marked for deletion from the original DataFrame.

        This function identifies rows that have been marked for deletion in `dataframe_displayed`
        and removes the corresponding rows from `dataframe_to_modify`.

        Parameters:
            dataframe_to_modify (pd.DataFrame): The original DataFrame from which rows will be removed.
            dataframe_displayed (pd.DataFrame): The DataFrame containing deletion flags.

        Returns:
            pd.DataFrame: The updated DataFrame with deleted rows removed.
        """
        # Apply deleted rows
        if self.get_deleted_rows():
            rows_to_delete = []
            for row in self.get_deleted_rows():
                row_index = self.get_index(row, dataframe_displayed)
                rows_to_delete.append(row_index)
            dataframe_to_modify.drop(index = rows_to_delete, inplace = True)
        return dataframe_to_modify

    def process_changes(self, dataframe_to_modify: pd.DataFrame, dataframe_displayed: pd.DataFrame, handle_deleted_rows : bool = False, column_deleted : str = None) -> pd.DataFrame:
        """
        Apply edits, additions, and deletions to the given DataFrame.

        This function processes changes made in `dataframe_displayed` and applies them to `dataframe_to_modify`.
        It handles:
        - Edits: Updates modified values in the original DataFrame.
        - Additions: Incorporates newly added rows.
        - Deletions: Removes rows marked for deletion.

        Parameters:
            dataframe_to_modify (pd.DataFrame): The original DataFrame to be updated.
            dataframe_displayed (pd.DataFrame): The modified DataFrame containing user edits, new rows, and deletion markers.

        Returns:
            pd.DataFrame: The updated DataFrame with all applied changes.
        """
        if handle_deleted_rows :
            dataframe_to_modify = self.apply_edited_rows_and_handle_deleted_rows(dataframe_to_modify, dataframe_displayed, column_deleted)
        else:
            dataframe_to_modify = self.apply_edited_rows(dataframe_to_modify, dataframe_displayed)
        dataframe_to_modify = self.apply_added_rows(dataframe_to_modify)
        dataframe_to_modify = self.apply_deleted_rows(dataframe_to_modify, dataframe_displayed)

        return dataframe_to_modify

