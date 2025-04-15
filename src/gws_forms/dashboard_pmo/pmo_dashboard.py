import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_sidebar import display_sidebar
from gws_forms.dashboard_pmo.pmo_project_plan_tab import display_project_plan_tab
from gws_forms.dashboard_pmo.pmo_gantt_tab import display_gantt_tab
from gws_forms.dashboard_pmo.pmo_plot_overview_tab import display_plot_overview_tab
from gws_forms.dashboard_pmo.pmo_details_tab import display_details_tab
from gws_forms.dashboard_pmo.pmo_todo_tab import display_todo_tab

def display_project_plan_page(pmo_table : PMOTable):
        display_project_plan_tab(pmo_table)

def display_gantt_page(pmo_table : PMOTable):
    display_gantt_tab(pmo_table)

def display_kpis_page(pmo_table : PMOTable):
    display_plot_overview_tab(pmo_table)

def display_notes_page(pmo_table : PMOTable):
    display_details_tab(pmo_table)

def display_milestones_page(pmo_table : PMOTable):
    display_todo_tab(pmo_table)

# Get pages
def get_project_plan_page(pmo_table : PMOTable):
    return st.Page(lambda:display_project_plan_page(pmo_table), title="Home", url_path='home', icon = ":material/home:")

def get_gantt_page(pmo_table : PMOTable):
    return st.Page(lambda:display_gantt_page(pmo_table), title="Gantt", url_path='gantt', icon = ":material/view_timeline:")

def get_kpis_page(pmo_table : PMOTable):
    return st.Page(lambda:display_kpis_page(pmo_table), title="KPIs", url_path='kpis', icon = ":material/analytics:")

def get_notes_page(pmo_table : PMOTable):
    return st.Page(lambda:display_notes_page(pmo_table), title="Notes", url_path='notes', icon = ":material/edit_note:")

def get_milestones_page(pmo_table : PMOTable):
    return st.Page(lambda:display_milestones_page(pmo_table), title="Milestones", url_path='milestones', icon = ":material/checklist:")

def show_content(pmo_table : PMOTable):
    display_sidebar(pmo_table)

    pg = st.navigation([get_project_plan_page(pmo_table), get_gantt_page(pmo_table), get_kpis_page(pmo_table), get_notes_page(pmo_table), get_milestones_page(pmo_table)])

    pg.run()

def run(pmo_table : PMOTable):
    show_content(pmo_table)