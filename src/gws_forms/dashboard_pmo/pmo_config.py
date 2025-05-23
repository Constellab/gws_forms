import streamlit as st
from gws_forms.dashboard_pmo.pmo_dto import ProjectDTO, MissionDTO
from gws_forms.dashboard_pmo.dialog_functions import delete_project, delete_mission, add_mission, edit_mission, edit_project, create_project
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_core.streamlit import StreamlitMenuButton, StreamlitMenuButtonItem


class PMOConfig():

    PMO_CONFIG_KEY = "pmo_config"

    @classmethod
    def get_instance(cls) -> "PMOConfig":
        if PMOConfig.PMO_CONFIG_KEY not in st.session_state:
            st.session_state[PMOConfig.PMO_CONFIG_KEY] = cls()
        return st.session_state[PMOConfig.PMO_CONFIG_KEY]

    @classmethod
    def store_instance(cls, instance: "PMOConfig") -> None:
        st.session_state[PMOConfig.PMO_CONFIG_KEY] = instance

    def build_new_project_button(self, pmo_table: PMOTable) -> bool:
        new_project_button = st.button(
            "New project", use_container_width=True, icon=":material/add:", type="primary",
            on_click=lambda: create_project(pmo_table))
        return new_project_button

    def build_new_mission_button(self, pmo_table: PMOTable, project: ProjectDTO) -> bool:
        new_mission_button = st.button(
            "New mission", use_container_width=True, icon=":material/add:",
            on_click=lambda: add_mission(pmo_table, project))
        return new_mission_button

    def build_project_menu_button(self, pmo_table: PMOTable, project: ProjectDTO) -> StreamlitMenuButton:
        button_menu_project = StreamlitMenuButton(key="button_menu_project")
        add_mission_button = StreamlitMenuButtonItem(label='Add mission', material_icon='add',
                                                     on_click=lambda: add_mission(pmo_table, project))
        button_menu_project.add_button_item(add_mission_button)
        edit_project_button = StreamlitMenuButtonItem(
            label='Edit project', material_icon='edit',
            on_click=lambda: edit_project(pmo_table, project))
        button_menu_project.add_button_item(edit_project_button)
        delete_project_button = StreamlitMenuButtonItem(
            label='Delete project', material_icon='delete', color='warn',
            on_click=lambda: delete_project(pmo_table, project))
        button_menu_project.add_button_item(delete_project_button)

        return button_menu_project

    def build_mission_menu_button(
            self, pmo_table: PMOTable, project: ProjectDTO, mission: MissionDTO) -> StreamlitMenuButton:
        button_menu_mission = StreamlitMenuButton(key=f"button_menu_mission_{mission.id}")

        # Create closure functions to capture the current values
        def make_edit_callback(pmo_table, p, m):
            return lambda: edit_mission(pmo_table, p, m)

        def make_delete_callback(pmo_table, p_id, m_id):
            return lambda: delete_mission(pmo_table, p_id, m_id)

        edit_mission_button = StreamlitMenuButtonItem(
            label='Edit mission',
            material_icon='edit',
            on_click=make_edit_callback(pmo_table, project, mission),
            key=f"edit_mission_{mission.id}")

        delete_mission_button = StreamlitMenuButtonItem(
            label='Delete mission',
            material_icon='delete',
            color='warn',
            on_click=make_delete_callback(pmo_table, project.id, mission.id),
            key=f"delete_mission_{mission.id}")

        button_menu_mission.add_button_item(edit_mission_button)
        button_menu_mission.add_button_item(delete_mission_button)
        return button_menu_mission
