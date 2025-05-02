import os
import json
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO
from gws_core.streamlit import rich_text_editor
from gws_core import RichText
from gws_forms.dashboard_pmo.pmo_project_plan_tab import display_project_plan_tab
from gws_forms.dashboard_pmo.pmo_gantt_tab import display_gantt_tab
from gws_forms.dashboard_pmo.pmo_plot_overview_tab import display_plot_overview_tab
from gws_forms.dashboard_pmo.pmo_details_tab import display_details_tab
from gws_forms.dashboard_pmo.pmo_settings import display_settings_tab
from gws_core.streamlit import StreamlitRouter


def display_project_plan_page(pmo_table: PMOTable):
    display_project_plan_tab(pmo_table)


def display_gantt_page(pmo_table: PMOTable):
    display_gantt_tab(pmo_table)


def display_kpis_page(pmo_table: PMOTable):
    display_plot_overview_tab(pmo_table)


def display_notes_page(pmo_table: PMOTable):
    display_details_tab(pmo_table)


def display_settings_page(pmo_table: PMOTable):
    display_settings_tab(pmo_table)


def add_home_page(router: StreamlitRouter, pmo_table: PMOTable):
    router.add_page(
        lambda: display_project_plan_page(pmo_table),
        title='Home',
        url_path='home',
        icon=":material/home:",
        hide_from_sidebar=False
    )


def add_gantt_page(router: StreamlitRouter, pmo_table: PMOTable):
    router.add_page(
        lambda: display_gantt_page(pmo_table),
        title='Gantt',
        url_path='gantt',
        icon=":material/view_timeline:",
        hide_from_sidebar=False
    )


def add_kpis_page(router: StreamlitRouter, pmo_table: PMOTable):
    router.add_page(
        lambda: display_kpis_page(pmo_table),
        title='KPIs',
        url_path='kpis',
        icon=":material/analytics:",
        hide_from_sidebar=False
    )


def add_notes_page(router: StreamlitRouter, pmo_table: PMOTable):
    router.add_page(
        lambda: display_notes_page(pmo_table),
        title='Notes',
        url_path='notes',
        icon=":material/edit_note:",
        hide_from_sidebar=True
    )


def add_settings_page(router: StreamlitRouter, pmo_table: PMOTable):
    router.add_page(
        lambda: display_settings_page(pmo_table),
        title='Settings',
        url_path='settings',
        icon=":material/settings:",
        hide_from_sidebar=False
    )


def show_content(pmo_table: PMOTable):
    # Get the last pmo_project_plan by default :
    # List all JSON files in the saved directory
    # TODO faire une fonction et la mettre aussi dans settings
    files = sorted([f.split(".json")[0] for f in os.listdir(
        pmo_table.folder_project_plan) if f.endswith(".json")], reverse=True)
    if files:
        selected_file = files[0] + ".json"
        file_path = os.path.join(
            pmo_table.folder_project_plan, selected_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            pmo_table.data = ProjectPlanDTO.from_json(loaded_data)
            pmo_table.processed_data = pmo_table._process_data()
            pmo_table.pmo_state.set_current_pmo_table(pmo_table)
    else:
        pmo_table.save_data_in_folder()
        pmo_table.pmo_state.set_current_pmo_table(pmo_table)

    router = StreamlitRouter.load_from_session()
    # Add pages
    add_home_page(router, pmo_table)
    add_gantt_page(router, pmo_table)
    add_kpis_page(router, pmo_table)
    add_notes_page(router, pmo_table)
    add_settings_page(router, pmo_table)

    router.run()


def run(pmo_table: PMOTable):
    show_content(pmo_table)
