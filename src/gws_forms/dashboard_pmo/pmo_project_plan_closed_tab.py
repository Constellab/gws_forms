import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status

def display_project_plan_closed_tab(pmo_table : PMOTable):
    """Display the DataFrame in Streamlit tabs. Here only the closed missions are presented"""
    pmo_table.pmo_state.get_df_to_save()
    pmo_table.pmo_state.get_active_project_plan(pmo_table.df)

    if not (
        pmo_table.pmo_state.active_project_plan(pmo_table.df, pmo_table.NAME_COLUMN_ACTIVE)
        [pmo_table.DEFAULT_COLUMNS_LIST].copy().reset_index(drop=True)
        .equals(pmo_table.df[pmo_table.DEFAULT_COLUMNS_LIST])
    ):
        st.warning("Please save your project plan first")
        return

    # Sort the DataFrame
    df_closed_projects = pmo_table.pmo_state.get_active_project_plan()[pmo_table.pmo_state.get_active_project_plan()[pmo_table.NAME_COLUMN_STATUS] == Status.CLOSED.value].copy(
    )
    if df_closed_projects.empty:
        st.write("No project is closed yet.")
        return
    if "index" in df_closed_projects.columns:
        df_closed_projects = df_closed_projects.drop(columns=[
                                                        "index"])
    if "level_0" in df_closed_projects.columns:
        df_closed_projects = df_closed_projects.drop(
            columns=["level_0"])
    st.dataframe(
        df_closed_projects[pmo_table.DEFAULT_COLUMNS_LIST], hide_index=True)
