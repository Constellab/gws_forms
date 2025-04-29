import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_sidebar import display_sidebar
from gws_forms.dashboard_pmo.pmo_project_plan_tab import display_project_plan_tab
from gws_forms.dashboard_pmo.pmo_gantt_tab import display_gantt_tab
from gws_forms.dashboard_pmo.pmo_plot_overview_tab import display_plot_overview_tab
from gws_forms.dashboard_pmo.pmo_details_tab import display_details_tab
from gws_forms.dashboard_pmo.pmo_todo_tab import display_todo_tab
from gws_core.streamlit import StreamlitRouter


def display_project_plan_page(pmo_table: PMOTable):
    display_project_plan_tab(pmo_table)


def display_gantt_page(pmo_table: PMOTable):
    display_gantt_tab(pmo_table)


def display_kpis_page(pmo_table: PMOTable):
    display_plot_overview_tab(pmo_table)


def display_notes_page(pmo_table: PMOTable):
    display_details_tab(pmo_table)


def display_milestones_page(pmo_table: PMOTable):
    display_todo_tab(pmo_table)


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


def add_milestones_page(router: StreamlitRouter, pmo_table: PMOTable):
    router.add_page(
        lambda: display_milestones_page(pmo_table),
        title='Milestones',
        url_path='milestones',
        icon=":material/checklist:",
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


def show_content(pmo_table: PMOTable):
    router = StreamlitRouter.load_from_session()
    display_sidebar(pmo_table)
    # Add pages
    add_home_page(router, pmo_table)
    add_gantt_page(router, pmo_table)
    add_kpis_page(router, pmo_table)
    add_milestones_page(router, pmo_table)
    add_notes_page(router, pmo_table)

    router.run()


def run(pmo_table: PMOTable):
    show_content(pmo_table)
