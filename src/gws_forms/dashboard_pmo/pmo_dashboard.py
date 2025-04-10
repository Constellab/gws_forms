import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_sidebar import display_sidebar
from gws_forms.dashboard_pmo.pmo_project_plan_tab import display_project_plan_tab
from gws_forms.dashboard_pmo.pmo_project_plan_closed_tab import display_project_plan_closed_tab
from gws_forms.dashboard_pmo.pmo_gantt_tab import display_gantt_tab
from gws_forms.dashboard_pmo.pmo_plot_overview_tab import display_plot_overview_tab
from gws_forms.dashboard_pmo.pmo_details_tab import display_details_tab
from gws_forms.dashboard_pmo.pmo_todo_tab import display_todo_tab

def display_tabs(pmo_table : PMOTable):
    display_sidebar(pmo_table)

    tab_widgets = {
        # Base tab widget
        "Home": display_project_plan_tab,
        "Closed projects": display_project_plan_closed_tab,
        "Gantt": display_gantt_tab,
        "KPIs": display_plot_overview_tab,
        "Notes": display_details_tab,
        "Milestones": display_todo_tab
    }

    names = list(tab_widgets.keys())
    widgets = list(tab_widgets.values())
    st_tabs = st.tabs(names)
    for idx, st_tab in enumerate(st_tabs):
        with st_tab:
            widgets[idx](pmo_table)
