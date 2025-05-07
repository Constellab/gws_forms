import os
import json
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_core.streamlit import rich_text_editor
from gws_core import RichText


def display_details_tab(pmo_table: PMOTable):

    # Display the details tab for the current mission
    project_selected = pmo_table.pmo_state.get_current_project().name
    mission_selected = pmo_table.pmo_state.get_current_mission().mission_name

    # Display note
    # Key for the file note - replace spaces with underscores
    key = f"{project_selected.replace(' ', '_')}_{mission_selected.replace(' ', '_')}"

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
        placeholder={f"{project_selected} - {mission_selected}"}, initial_value=rich_text, key=key)

    if result:
        # saving modified rich text to json file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dto_json_dict(), f)
