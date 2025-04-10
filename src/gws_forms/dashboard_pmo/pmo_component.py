import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable

def check_if_project_plan_is_edited(pmo_table : PMOTable) -> bool:
    """
    Checks if the project plan has been edited by comparing the filtered DataFrame
    with the edited project plan.

    Args:
        pmo_table (PMOTable): The PMO table

    Returns:
        bool: True if the project plan is edited, False otherwise.
    """
    is_edited = pmo_table.table_editing_state
    if is_edited :
        st.warning("Please save your project plan first")

    return is_edited

def check_if_project_plan_is_edited_sidebar(pmo_table : PMOTable) -> None:
    if pmo_table.table_editing_state:
        with st.sidebar:
            pmo_table.placeholder_warning_filtering.error(
                "Save your project plan before filtering.", icon="🚨")
