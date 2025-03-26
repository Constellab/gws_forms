import json
import pandas as pd
import streamlit as st

class Etable:
    TEXT = "text"
    NUMERIC = "numeric"
    DATE = "date"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"

    def __init__(self, json_path : str = None):
        self.json_path = json_path
        if self.json_path:
            self.json_data = self._load_json()
            self.df = self._prepare_dataframe()
        else :
            self.json_data = {}
            self.df = pd.DataFrame()

    def _load_json(self):
        try:
            with open(self.json_path, 'r', encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise ValueError(f"The file at {self.json_path} was not found.")
        except json.JSONDecodeError:
            raise ValueError(f"The file at {self.json_path} is not a valid JSON.")


    def _prepare_dataframe(self):
        """Converts JSON data into a DataFrame with correct types."""
        df = pd.json_normalize(self.json_data["data"])
        column_types = self.json_data.get("column_types", {})
        for column, col_type in column_types.items():
            if col_type == self.NUMERIC:
                df[column] = df[column].astype(float)
            elif col_type == self.DATE:
                df[column] = df[column].fillna('').astype('datetime64[ns]')
            elif col_type == self.BOOLEAN:
                df[column] = df[column].astype(bool)
            elif col_type == self.CATEGORICAL:
                df[column] = df[column].astype("category")
        return df


    def download(self, file_format : str ="csv"):
        """Download the DataFrame as CSV or JSON."""
        if file_format == "csv":
            return self.df.to_csv(index=False)
        elif file_format == "json":
            return self.df.to_json(orient="records", indent=2)

    def display(self):
        """Display the DataFrame."""
        st.dataframe(self.df)
