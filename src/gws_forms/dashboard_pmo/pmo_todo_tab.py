import os
from datetime import datetime
import pytz
import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Event
from gws_forms.dashboard_pmo._dashboard_code.container.container import st_fixed_container


def process_mission(row, pmo_table : PMOTable, project_name : str, updated_milestones : dict, number_project : int):
    mission_name = row[pmo_table.NAME_COLUMN_MISSION_NAME]
    milestones = row[pmo_table.NAME_COLUMN_MILESTONES]

    if milestones == "nan":
        updated_milestones[pmo_table.get_index(row.name)] = ""
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

        checked_task = st.checkbox(
            label=f"~~{task}~~" if is_completed else task,
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
    updated_milestones[pmo_table.get_index(row.name)] = "\n".join(
        updated_task_list)


def display_todo_tab(pmo_table : PMOTable):
    pmo_table.pmo_state.get_df_to_save()
    pmo_table.pmo_state.get_active_project_plan(pmo_table.df)

    if not (
        pmo_table.pmo_state.active_project_plan(pmo_table.df, pmo_table.NAME_COLUMN_ACTIVE)
        [pmo_table.DEFAULT_COLUMNS_LIST].copy().reset_index(drop=True)
        .equals(pmo_table.df[pmo_table.DEFAULT_COLUMNS_LIST])
    ):
        st.warning("Please save your project plan first")
        return

    pmo_table.df = pmo_table.validate_columns(pmo_table.df)
    pmo_table.pmo_state.set_active_project_plan(pmo_table.validate_columns(pmo_table.pmo_state.get_active_project_plan()))

    # Filter the relevant columns
    filtered_df = pmo_table.df[[pmo_table.NAME_COLUMN_PROJECT_NAME,
                            pmo_table.NAME_COLUMN_MISSION_NAME, pmo_table.NAME_COLUMN_MILESTONES]]

    if not (not filtered_df.empty and (filtered_df[pmo_table.NAME_COLUMN_MILESTONES] != "nan").any()):
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
        if (group[pmo_table.NAME_COLUMN_MILESTONES] != "nan").any():
            st.subheader(f"**Project:** {project_name}")
            group.apply(process_mission, args = (pmo_table, project_name, updated_milestones, number_project, ), axis=1)
        number_project += 1

    pmo_table.pmo_state.get_show_success_todo()

    with st_fixed_container(mode="sticky", position="bottom", border=False, transparent=False):
        cols = st.columns([1, 2])
        with cols[0]:
            if st.button("Update infos", use_container_width=False, icon=":material/save:"):
                # Apply the updates to the original DataFrame
                for index, new_milestones in updated_milestones.items():
                    pmo_table.pmo_state.get_active_project_plan().at[index,
                                                                pmo_table.NAME_COLUMN_MILESTONES] = new_milestones

                # Save updated DataFrame to session state
                pmo_table.pmo_state.set_df_to_save(pmo_table.pmo_state.get_active_project_plan())
                pmo_table.pmo_state.set_df_to_save(pmo_table.validate_columns(pmo_table.pmo_state.get_df_to_save()))
                pmo_table.df = pmo_table.pmo_state.get_df_to_save().copy()
                # Save dataframe in the folder
                timestamp = datetime.now(tz=pytz.timezone(
                    'Europe/Paris')).strftime("plan_%Y-%m-%d-%Hh%M.csv")
                path = os.path.join(
                    pmo_table.folder_project_plan, timestamp)
                pmo_table.pmo_state.get_df_to_save().to_csv(
                    path, index=False)
                # Apply the observer -> Update tag folder
                if pmo_table.observer :
                    check = pmo_table.observer.update(Event(event_type='update_line'))
                    if not check:
                        raise Exception ("Something got wrong, close the app and try again.")
                pmo_table.pmo_state.set_show_success_todo(True)
                st.rerun()
        with cols[1]:
            if pmo_table.pmo_state.get_show_success_todo():
                st.success("Changes saved!")

    if pmo_table.pmo_state.get_show_success_todo():
        pmo_table.pmo_state.set_show_success_todo(False)
