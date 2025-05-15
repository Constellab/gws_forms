import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority, Event
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO, MilestoneDTO
from gws_forms.dashboard_pmo.pmo_config import PMOConfig
from gws_forms.dashboard_pmo.dialog_functions import delete_milestone,  add_milestone, edit_milestone
from gws_core.streamlit import StreamlitMenuButton, StreamlitRouter, StreamlitMenuButtonItem, StreamlitContainers, StreamlitHelper


def update_milestone(pmo_table: PMOTable, key: str, milestone: MilestoneDTO):
    """Update the milestone status when the checkbox is clicked."""
    # Update the milestone status
    st.write(milestone.id)
    pmo_table.update_milestone_status_by_id(milestone.id, st.session_state[key])
    pmo_table.commit_and_save()
    # TODO mettre l'observer ici
    """# Apply the observer -> Update tag folder
    if pmo_table.observer:
        check = pmo_table.observer.update(Event(event_type='update_line'))
        if not check:
            raise Exception("Something got wrong, close the app and try again.")"""


def display_project_plan_tab(pmo_table: PMOTable):
    """Display the DataFrame in Streamlit tabs."""
    router = StreamlitRouter.load_from_session()
    # Define the variable pmo_state
    pmo_state = pmo_table.pmo_state
    pmo_config = PMOConfig.get_instance()

    # Display success message in a toast format
    pmo_state.display_success_message()

    # Create two columns for layout
    left_col, right_col = st.columns([1, 4])

    # Left column - Project list
    with left_col:
        pmo_config.build_new_project_button(pmo_table)

        # Get unique project names, ordered alphabetically
        project_names = sorted(list(set(project.name for project in pmo_table.data.data)))

        # Create radio buttons for project selection
        selected_project = st.radio(
            "Select a project",
            options=project_names,
            index=project_names.index(pmo_state.get_current_project().name) if pmo_state.get_current_project() else 0,
            label_visibility="collapsed"
        )
        project_id = ProjectPlanDTO.get_project_by_name(pmo_table.data, selected_project).id
        project = ProjectPlanDTO.get_project_by_id(pmo_table.data, project_id)

    # Right column - Project details
    with right_col:
        if project:
            pmo_table.pmo_state.set_current_project(project)
            # Create a container for the header with project title and action buttons
            header_col1, header_col2 = st.columns([6, 1])
            with header_col1:
                st.header(f"{project.name}")
            with header_col2:

                button_project: StreamlitMenuButton = pmo_config.build_project_menu_button(pmo_table, project)
                button_project.render()

            project_data = []
            # Filter data for selected project
            for project in pmo_table.data.data:
                if project.id == project_id:
                    # Get the project data
                    project_data = project.missions
            # If there is no mission set yet, return
            if not project_data:
                return
            # Define status order mapping
            status_order = Status.get_order()

            # Sort project_data by status first, then mission name
            project_data.sort(key=lambda x: (
                status_order.get(x.status),  # Status order
                x.mission_name.lower()  # Mission name alphabetically
            ))

            # Display project information
            for mission in project_data:
                mission_name = mission.mission_name
                pmo_table.pmo_state.set_current_mission(mission)
                mission_id = mission.id
                st.markdown("---")

                header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
                with header_col1:
                    st.subheader(mission_name)
                with header_col2:
                    # Open note in a hidden page
                    if st.button("View note", icon=":material/visibility:", use_container_width=True,
                                 key=f"view_note_{mission_id}"):
                        router.navigate('notes')
                with header_col3:

                    pmo_config = PMOConfig.get_instance()
                    button_mission: StreamlitMenuButton = pmo_config.build_mission_menu_button(
                        pmo_table, project, mission)
                    button_mission.render()

                col1, col2, col3 = st.columns(3)

                # Only display if priority exists
                priority = mission.priority
                if priority and priority != Priority.NONE.value:
                    with col1:
                        st.write(priority)

                # Only display if status exists
                status = mission.status
                if status and status != Status.NONE.value:
                    with col2:
                        st.write(status)

                # Only display if progress exists
                progress = mission.progress
                if progress is not None:
                    with col3:
                        # Display progress as a percentage
                        st.write(f"{str(progress)}%")

                # Only display referee if exists
                referee = mission.mission_referee
                if referee:
                    st.markdown(f"**{pmo_table.NAME_COLUMN_MISSION_REFEREE}:** {referee}")

                # Only display dates if they exist
                start_date = mission.start_date
                end_date = mission.end_date
                if start_date or end_date:
                    date_str = f"{start_date if start_date else ''}"
                    date_str += f" **-** {end_date if end_date else ''}"
                    st.markdown(f"**Date:** {date_str}")

                # Only display team members if exists
                team_members = mission.team_members
                if team_members and team_members != "No members" and team_members != [""]:
                    team_members_str = ", ".join(team_members)
                    st.markdown(f"**{pmo_table.NAME_COLUMN_TEAM_MEMBERS}:** {team_members_str}")

                # Milestones
                milestones = mission.milestones
                title_col, button_col = StreamlitContainers.columns_with_fit_content(
                    key=f"milestone_container_{mission_id}",
                    cols=[1, 'fit-content'])
                with button_col:
                    st.button("Add milestone", icon=":material/add:",
                              use_container_width=True,
                              key=f"add_milestone_{mission_id}",
                              on_click=add_milestone,
                              args=(pmo_table, project_id, mission_id,))
                # Only display milestones if exists
                if milestones:
                    with title_col:
                        st.markdown(f"**{pmo_table.NAME_COLUMN_MILESTONES}:**")
                    i = 0
                    for milestone in milestones:
                        button_key = f"edit_milestone_{i}_{mission_id}"
                        button_css_class = StreamlitHelper.get_element_css_class(button_key)
                        col1, col2 = StreamlitContainers.columns_with_fit_content(
                            f'milestone_{i}_{mission_id}', cols=[1, 'fit-content'],
                            additional_style=f"""
                                                                                [CLASS_NAME] .{button_css_class} {{
                                                                                    opacity: 0;
                                                                                }}

                                                                                [CLASS_NAME]:hover .{button_css_class} {{
                                                                                    opacity: 1;
                                                                                }}
                                                                                """)

                        name = milestone.name
                        done = milestone.done

                        with col1:

                            # Format the milestone display
                            task_label = f"~~{name.strip()}~~" if done else name
                            key = f"{name}_{project_id}_{mission_id}_{i}"

                            st.checkbox(
                                label=task_label,
                                key=key,
                                value=done,
                                on_change=update_milestone,
                                args=(pmo_table, key, milestone,))

                        with col2:
                            button_menu_milestone = StreamlitMenuButton(key=button_key)
                            edit_milestone_button = StreamlitMenuButtonItem(
                                label='Edit milestone', material_icon='edit',
                                on_click=lambda milestone=milestone: edit_milestone(pmo_table, milestone.id))
                            button_menu_milestone.add_button_item(edit_milestone_button)
                            delete_milestone_button = StreamlitMenuButtonItem(
                                label='Delete milestone', material_icon='delete', color='warn',
                                on_click=lambda mission_id=mission_id,
                                milestone=milestone: delete_milestone(pmo_table, project_id, mission_id, milestone))
                            button_menu_milestone.add_button_item(delete_milestone_button)

                            button_menu_milestone.render()

                        i += 1

    # TODO apply the observer somewhere
    """# Apply the observer -> Update tag folder
    if pmo_table.observer:
        check = pmo_table.observer.update(Event(event_type='update_line'))
        if not check:
            raise Exception("Something got wrong, close the app and try again.")"""
