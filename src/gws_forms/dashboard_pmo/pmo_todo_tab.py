import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Event
from gws_forms.dashboard_pmo.pmo_dto import MilestoneDTO
from gws_forms.dashboard_pmo._dashboard_code.container.container import st_fixed_container


def process_mission(mission_data: dict, pmo_table: PMOTable, project_name: str, updated_milestones: dict,
                    number_project: int):
    mission_name = mission_data[pmo_table.NAME_COLUMN_MISSION_NAME]
    milestones = mission_data[pmo_table.NAME_COLUMN_MILESTONES]
    mission_id = mission_data[pmo_table.NAME_COLUMN_UNIQUE_ID]

    if not milestones or milestones == '/':
        updated_milestones[mission_id] = []
        return

    # Display mission name before the tasks
    st.write(f"**Mission:** {mission_name}")

    # Process milestones list
    updated_milestone_list = []
    for idx, milestone in enumerate(milestones):
        # Convert dict to MilestoneDTO if needed
        milestone = MilestoneDTO(**milestone) if not isinstance(milestone, MilestoneDTO) else milestone

        task_label = f"~~{milestone.name.strip()}~~" if milestone.done else milestone.name
        checked_task = st.checkbox(
            label=task_label,
            key=f"{project_name}_{mission_name}_{milestone.name}_{number_project}_{mission_id}_{idx}",
            value=milestone.done
        )

        # Update milestone status
        milestone.done = checked_task
        updated_milestone_list.append(milestone)

    # Store updated milestones for this mission
    updated_milestones[mission_id] = updated_milestone_list


def display_todo_tab(pmo_table: PMOTable):
    # Define the variable pmo_state
    pmo_state = pmo_table.pmo_state

    # Group missions by project
    projects = {}
    for mission in pmo_table.processed_data:
        project_name = mission[pmo_table.NAME_COLUMN_PROJECT_NAME]
        if mission[pmo_table.NAME_COLUMN_MILESTONES] and mission[pmo_table.NAME_COLUMN_MILESTONES] != '/':
            if project_name not in projects:
                projects[project_name] = []
            projects[project_name].append(mission)

    if not projects:
        st.warning(f"Please complete the {pmo_table.NAME_COLUMN_MILESTONES} column first ")
        return

    updated_milestones = {}

    # Iterate through each project
    number_project = 0
    for project_name, missions in projects.items():
        with st.expander(f"**Project:** {project_name}", expanded=True):
            st.subheader(f"**Project:** {project_name}")
            for mission in missions:
                process_mission(mission, pmo_table, project_name, updated_milestones, number_project)
        number_project += 1

    pmo_state.get_show_success_todo()

    with st_fixed_container(mode="sticky", position="bottom", border=False, transparent=False):
        cols = st.columns([1, 2])
        with cols[0]:
            if st.button("Update infos", use_container_width=False, icon=":material/save:"):
                # Apply the updates to the processed data
                for mission in pmo_table.processed_data:
                    mission_id = mission[pmo_table.NAME_COLUMN_UNIQUE_ID]
                    if mission_id in updated_milestones:
                        mission[pmo_table.NAME_COLUMN_MILESTONES] = [
                            milestone.model_dump() if isinstance(milestone, MilestoneDTO) else milestone
                            for milestone in updated_milestones[mission_id]
                        ]

                # Save updated data and validate
                # pmo_table.validate_columns()
                pmo_table.save_data_in_folder()

                # Apply the observer -> Update tag folder
                if pmo_table.observer:
                    check = pmo_table.observer.update(Event(event_type='update_line'))
                    if not check:
                        raise Exception("Something got wrong, close the app and try again.")
                pmo_state.set_show_success_todo(True)
                st.rerun()
        with cols[1]:
            if pmo_state.get_show_success_todo():
                st.success("Changes saved!")

    if pmo_state.get_show_success_todo():
        pmo_state.set_show_success_todo(False)
