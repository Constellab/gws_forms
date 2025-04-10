import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_component import check_if_project_plan_is_edited

def display_project_plan_closed_tab(pmo_table : PMOTable):
    """Display the DataFrame in Streamlit tabs. Here only the closed missions are presented"""
    if check_if_project_plan_is_edited(pmo_table):
        return

    # Sort the DataFrame
    df_closed_projects = pmo_table.get_filter_df(only_closed_status = True)
    if df_closed_projects.empty:
        st.write("No project is closed yet.")
        return
    if "index" in df_closed_projects.columns:
        df_closed_projects = df_closed_projects.drop(columns=["index"])
    if "level_0" in df_closed_projects.columns:
        df_closed_projects = df_closed_projects.drop(columns=["level_0"])
    st.dataframe(
        df_closed_projects[pmo_table.DEFAULT_COLUMNS_LIST], hide_index=True)
