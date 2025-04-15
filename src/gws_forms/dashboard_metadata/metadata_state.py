import os
import json
from typing import List, Dict

import streamlit as st
from gws_core import StringHelper

class MetadataState():

    NAME_METADATA_KEY = 'name_metadata'
    METADATA_TYPE_KEY = 'metadata_type'
    ALLOWED_VALUES_KEY = 'allowed_values'
    DESCRIPTION_KEY = 'description'
    MIN_VALUE_KEY = 'min_value'
    MAX_VALUE_KEY = 'max_value'
    # User keys
    NAME_METADATA_USER_KEY = 'name_metadata_user'
    METADATA_TYPE_USER_KEY = 'metadata_type_user'
    ALLOWED_VALUES_USER_KEY = 'allowed_values_user'
    DESCRIPTION_USER_KEY = 'description_user'
    MIN_VALUE_USER_KEY = 'min_value_user'
    MAX_VALUE_USER_KEY = 'max_value_user'

    ALLOWED_VALUES_NUMBER_KEY = "allowed_values_number"

    path = None

    def __init__(self, folder_metadata : str) -> None:
        self.path = os.path.join(folder_metadata, "metadata.json")

    def get_allowed_values_number(self) -> int :
        return st.session_state.get(self.ALLOWED_VALUES_NUMBER_KEY, 1)

    def set_allowed_values_number(self, value : str) -> None:
        st.session_state[self.ALLOWED_VALUES_NUMBER_KEY] = value

    def get_metadata_json(self) -> Dict:
        # Load the JSON file if exist
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8') as f:
                metadata_json = json.load(f)
        else :
            metadata_json = {}

        # Ensure "metadata" key is a list
        if "metadata" not in metadata_json or not isinstance(metadata_json["metadata"], list):
            metadata_json["metadata"] = []

        return metadata_json

    def save_metadata_json(self, new_metadata_json : Dict) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(new_metadata_json, f, ensure_ascii=False, indent=2)

    def get_min_value(self) -> List:
        # It's the value of the number input min value
        return st.session_state.get(self.MIN_VALUE_KEY, None)

    def set_min_value(self, value : str) -> None:
        st.session_state[self.MIN_VALUE_KEY] = value

    def get_max_value(self) -> List:
        # It's the value of the number input max value
        return st.session_state.get(self.MAX_VALUE_KEY, None)

    def set_max_value(self, value : str) -> None:
        st.session_state[self.MAX_VALUE_KEY] = value

    def get_name_metadata(self) -> List:
        # It's the value of the text input Name
        return st.session_state.get(self.NAME_METADATA_KEY, [])

    def set_name_metadata(self, value : str) -> None:
        st.session_state[self.NAME_METADATA_KEY] = value

    def get_metadata_type(self) -> List:
        # It's the value of the text input metadata type
        return st.session_state.get(self.METADATA_TYPE_KEY, [])

    def set_metadata_type(self, value : str) -> None:
        st.session_state[self.METADATA_TYPE_KEY] = value

    def get_allowed_values_by_number(self, number : int) -> str:
        # It's the value of the text input allowed_values
        return st.session_state.get(self.ALLOWED_VALUES_KEY + f"_{number}", "")

    def set_allowed_values_by_number(self, number : int, value : str) -> None:
        st.session_state[self.ALLOWED_VALUES_KEY + f"_{number}"] = value

    def get_description(self) -> List:
        # It's the value of the text input description
        return st.session_state.get(self.DESCRIPTION_KEY, [])

    def set_description(self, value : str) -> None:
        st.session_state[self.DESCRIPTION_KEY] = value


    # Keep values entered by the user
    # Set
    def set_name_metadata_user(self, value : str) -> None:
        st.session_state[self.NAME_METADATA_USER_KEY] = value

    def set_description_user(self, value : str) -> None:
        st.session_state[self.DESCRIPTION_USER_KEY] = value

    def set_allowed_values_user(self, value : str) -> None:
        st.session_state[self.ALLOWED_VALUES_USER_KEY] = value

    def set_metadata_type_user(self, value : str) -> None:
        st.session_state[self.METADATA_TYPE_USER_KEY] = value

    def set_min_value_user(self, value : str) -> None:
        st.session_state[self.MIN_VALUE_USER_KEY] = value

    def set_max_value_user(self, value : str) -> None:
        st.session_state[self.MAX_VALUE_USER_KEY] = value

    # Get
    def get_name_metadata_user(self) -> List:
        return st.session_state.get(self.NAME_METADATA_USER_KEY, [])

    def get_description_user(self) -> List:
        return st.session_state.get(self.DESCRIPTION_USER_KEY, [])

    def get_allowed_values_user(self) -> List:
        return st.session_state.get(self.ALLOWED_VALUES_USER_KEY, [])

    def get_metadata_type_user(self) -> List:
        return st.session_state.get(self.METADATA_TYPE_USER_KEY, [])

    def get_min_value_user(self) -> List:
        return st.session_state.get(self.MIN_VALUE_USER_KEY, None)

    def get_max_value_user(self) -> List:
        return st.session_state.get(self.MAX_VALUE_USER_KEY, None)


    def clear_fields(self) -> None:
        # Save the values entered by the user
        self.set_name_metadata_user(self.get_name_metadata())
        self.set_description_user(self.get_description())
        list_allowed_values = []
        for i in range(1, self.get_allowed_values_number() + 1):
            value = self.get_allowed_values_by_number(i)
            if value :
                list_allowed_values.append(value)
        self.set_allowed_values_user(list_allowed_values)
        self.set_metadata_type_user(self.get_metadata_type())
        self.set_min_value_user(self.get_min_value())
        self.set_max_value_user(self.get_max_value())

        # Clear the different fields
        self.set_name_metadata('')
        self.set_description('')
        for i in range(1, self.get_allowed_values_number() + 1):
            self.set_allowed_values_by_number(i, '')
        self.set_metadata_type('options')
        self.set_min_value(0)
        self.set_max_value(0)
        self.set_allowed_values_number(1)

    def get_new_entry(self) -> Dict:
        return {
                "unique_id": StringHelper.generate_uuid(),
                "name": self.get_name_metadata_user(),
                "description": self.get_description_user(),
                "response_type": self.get_metadata_type_user(),
                "allowed_values": self.get_allowed_values_user(),
                "min_value": self.get_min_value_user() if self.get_metadata_type_user() == "numeric" else None,
                "max_value": self.get_max_value_user() if self.get_metadata_type_user() == "numeric" else None,
            }

    def get_existing_entry(self, value_user : bool = False) -> Dict:
        if value_user :
            name = self.get_name_metadata_user()
        else :
            name = self.get_name_metadata()
        return next((item for item in self.get_metadata_json()["metadata"] if item["name"] == name), None)