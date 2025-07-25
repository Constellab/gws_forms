import os
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_core.streamlit import rich_text_editor, StreamlitRouter
from gws_core import RichText
import streamlit as st


def display_details_tab(pmo_table: PMOTable):
    # Add return button at the top
    router = StreamlitRouter.load_from_session()
    if st.button("Return", icon=":material/arrow_back:", use_container_width=False):
        router.navigate('mission')

    # Display the details tab for the current mission
    project_selected = pmo_table.pmo_state.get_current_project()
    mission_selected = pmo_table.pmo_state.get_current_mission()

    # Display note
    # Key for the file note - replace spaces with underscores
    key = f"{project_selected.id.replace(' ', '_')}_{mission_selected.id.replace(' ', '_')}"

    file_path = os.path.join(
        pmo_table.folder_details, f'{key}.json')

    if os.path.exists(file_path):
        # initialising the rich text from a json file
        rich_text: RichText = RichText.from_json_file(file_path)
    else:
        rich_text: RichText = RichText()

    # calling component
    result = rich_text_editor(
        placeholder=f"{project_selected.name} - {mission_selected.mission_name}", initial_value=rich_text, key=key)

    if not result.is_empty():
        # saving modified rich text to json file
        result.to_json_file(file_path)
