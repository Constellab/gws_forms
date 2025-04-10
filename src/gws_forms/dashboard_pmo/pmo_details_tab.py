import os
import json
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_component import check_if_project_plan_is_edited
from gws_core.streamlit import rich_text_editor
from gws_core import RichText

def display_details_tab(pmo_table : PMOTable):
    if check_if_project_plan_is_edited(pmo_table):
        return

    cols_1 = st.columns(2)
    list_projects = pmo_table.get_filter_df()[pmo_table.NAME_COLUMN_PROJECT_NAME].unique()
    if len(list_projects) == 0 :
        st.warning(
            f"Please complete the {pmo_table.NAME_COLUMN_PROJECT_NAME} column first")
        return

    with cols_1[0]:
        project_selected: str = st.selectbox(
            label=r"$\textbf{\textsf{\large{Choose a project}}}$", options=list_projects)
    if project_selected:
        list_missions = pmo_table.get_filter_df()[pmo_table.get_filter_df()[pmo_table.NAME_COLUMN_PROJECT_NAME]
                                == project_selected][pmo_table.NAME_COLUMN_MISSION_NAME]
        with cols_1[1]:
            mission_selected: str = st.selectbox(
                label=r"$\textbf{\textsf{\large{Choose a mission}}}$", options=list_missions)
        if mission_selected:
            # Display note
            # Key for the file note
            key = f"{project_selected}_{mission_selected}"

            file_path = os.path.join(
                pmo_table.folder_details, f'{key}.json')
            # initialising the rich text from a json file
            rich_text: RichText = None
            if os.path.exists(file_path):
                # load json file to rich text
                with open(file_path, 'r', encoding='utf-8') as f:
                    rich_text = RichText.from_json(json.load(f))
            else:
                rich_text = RichText()

            # calling component
            result = rich_text_editor(
                placeholder=key, initial_value=rich_text, key=key)

            if result:
                # saving modified rich text to json file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(result.to_dto_json_dict(), f)
