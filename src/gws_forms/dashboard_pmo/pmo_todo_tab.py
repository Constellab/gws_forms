import pandas as pd
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Event
from gws_forms.dashboard_pmo._dashboard_code.container.container import st_fixed_container
from gws_forms.dashboard_pmo.streamlit_data_editor import StreamlitDataEditor
from gws_forms.dashboard_pmo.pmo_component import check_if_project_plan_is_edited

def process_mission(row, pmo_table : PMOTable, project_name : str, updated_milestones : dict, number_project : int):
    mission_name = row[pmo_table.NAME_COLUMN_MISSION_NAME]
    milestones = row[pmo_table.NAME_COLUMN_MILESTONES]

    if pd.isna(milestones):
        index = StreamlitDataEditor(dataframe_displayed = pmo_table.df, key = "editor").get_row_by_unique_id(row.name, pmo_table.df, pmo_table.NAME_COLUMN_UNIQUE_ID)
        updated_milestones[index] = ""
        return

    # Split milestones into individual tasks
    task_list = milestones.split("\n")

    # Display mission name before the tasks
    st.write(f"**Mission:** {mission_name}")

    updated_task_list = []
    number_task = 0
    for task in task_list:
        # Check if the task is marked as completed
        is_completed = task.startswith("✅")
        task_label = f"~~{task.strip()}~~" if is_completed else task

        checked_task = st.checkbox(
            label=task_label,
            key=f"{project_name}_{mission_name}_{task}_{number_project}_{row.name}_{number_task}", value=is_completed)

        # Update the task's status
        if checked_task:
            task = f"✅{task[1:]}" if task.startswith(
                "-") else task
        else:
            task = f"-{task[1:]}" if task.startswith(
                "✅") else task

        updated_task_list.append(task)
        number_task += 1

    # Store updated tasks back in the milestones for this mission
    index = StreamlitDataEditor(dataframe_displayed = pmo_table.df, key = "editor").get_row_by_unique_id(row.name, pmo_table.df, pmo_table.NAME_COLUMN_UNIQUE_ID)
    updated_milestones[index] = "\n".join(updated_task_list)

def display_todo_tab(pmo_table : PMOTable):
    # Define the variable pmo_state
    pmo_state = pmo_table.pmo_state

    if check_if_project_plan_is_edited(pmo_table):
        return

    # Filter the relevant columns
    filtered_df = pmo_table.get_filter_df()[[pmo_table.NAME_COLUMN_PROJECT_NAME,
                            pmo_table.NAME_COLUMN_MISSION_NAME, pmo_table.NAME_COLUMN_MILESTONES]]

    if not (not filtered_df.empty and pd.notna(filtered_df[pmo_table.NAME_COLUMN_MILESTONES]).any()):
        st.warning(
                f"Please complete the {pmo_table.NAME_COLUMN_MILESTONES} column first ")
        return

    updated_milestones = {}
    # Group by project name
    grouped_by_project = filtered_df.groupby(
        pmo_table.NAME_COLUMN_PROJECT_NAME)

    # Iterate through each project
    number_project = 0
    for project_name, group in grouped_by_project:
        if pd.notna(group[pmo_table.NAME_COLUMN_MILESTONES]).any():
            with st.expander(f"**Project:** {project_name}", expanded= True):
                st.subheader(f"**Project:** {project_name}")
                group.apply(process_mission, args = (pmo_table, project_name, updated_milestones, number_project, ), axis=1)
        number_project += 1

    pmo_state.get_show_success_todo()

    with st_fixed_container(mode="sticky", position="bottom", border=False, transparent=False):
        cols = st.columns([1, 2])
        with cols[0]:
            if st.button("Update infos", use_container_width=False, icon=":material/save:"):
                # Apply the updates to the original DataFrame
                for index, new_milestones in updated_milestones.items():
                    pmo_table.df.at[index,pmo_table.NAME_COLUMN_MILESTONES] = new_milestones

                # Save updated DataFrame to session state
                pmo_table.validate_columns()
                # Save dataframe in the folder
                pmo_table.save_df_in_folder()
                # Apply the observer -> Update tag folder
                if pmo_table.observer :
                    check = pmo_table.observer.update(Event(event_type='update_line'))
                    if not check:
                        raise Exception ("Something got wrong, close the app and try again.")
                pmo_state.set_show_success_todo(True)
                st.rerun()
        with cols[1]:
            if pmo_state.get_show_success_todo():
                st.success("Changes saved!")

    if pmo_state.get_show_success_todo():
        pmo_state.set_show_success_todo(False)
