import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO, MilestoneDTO
from gws_forms.dashboard_pmo.pmo_config import PMOConfig
from gws_forms.dashboard_pmo.dialog_functions import delete_milestone, add_milestone, edit_milestone
from gws_core.streamlit import StreamlitTreeMenu, StreamlitTreeMenuItem, StreamlitMenuButton, StreamlitRouter, StreamlitMenuButtonItem, StreamlitContainers, StreamlitHelper

def update_milestone(pmo_table: PMOTable, key: str, milestone: MilestoneDTO):
    """Update the milestone status when the checkbox is clicked."""
    # Update the milestone status
    pmo_table.update_milestone_status_by_id(milestone.id, st.session_state[key])
    pmo_table.commit_and_save()

def build_tree_menu_from_data(pmo_table: PMOTable):
    button_menu = StreamlitTreeMenu(key = pmo_table.pmo_state.TREE_PMO_KEY)
    clients_list = ProjectPlanDTO.get_clients(pmo_table.data)
    # Sort project data by client name
    clients_list.sort(key=lambda x: x.client_name.lower())

    # Build nodes from actual data: Client > Project > Mission
    # Build the tree structure
    for client in clients_list:
        client_item = StreamlitTreeMenuItem(
            label=client.client_name,
            key=client.id,
            material_icon='person'
        )
        for project in client.projects:
            project_item = StreamlitTreeMenuItem(
                label=project.name,
                key=project.id,
                material_icon='folder'
            )

            # Define status order mapping
            status_order = Status.get_order()

            # Sort project data by status first, then mission name
            project.missions.sort(key=lambda x: (
                status_order.get(x.status),  # Status order
                x.mission_name.lower()  # Mission name alphabetically
            ))

            for mission in project.missions:
                mission_item = StreamlitTreeMenuItem(
                    label=mission.mission_name,
                    key=mission.id,
                    material_icon='description'
                )
                project_item.add_children([mission_item])
            client_item.add_children([project_item])
        button_menu.add_item(client_item)
    return button_menu, clients_list


def display_mission_tab(pmo_table: PMOTable):
    # Define the variable pmo_state
    pmo_state = pmo_table.pmo_state
    pmo_config = PMOConfig.get_instance()

    # Display success message in a toast format
    pmo_state.display_success_message()

    router = StreamlitRouter.load_from_session()
    # Create two columns for layout
    left_col, right_col = st.columns([1, 4])

    # Left column - Project list
    with left_col:
        # Button to create a new project
        pmo_config.build_new_project_button(pmo_table)
        return_select: StreamlitTreeMenuItem = None
        # Build and render the tree menu
        button_menu_tree, clients_list = build_tree_menu_from_data(pmo_table)

        # Set a default selected item
        if pmo_state.get_current_mission():
            button_menu_tree.set_default_selected_item(pmo_state.get_current_mission().id)
        elif pmo_state.get_current_project():
            button_menu_tree.set_default_selected_item(pmo_state.get_current_project().id)
        else:
            client = clients_list[0]
            if client.projects:
                project = client.projects[0]
                if project.missions:
                    button_menu_tree.set_default_selected_item(project.missions[0].id)
                else:
                    button_menu_tree.set_default_selected_item(project.id)
            else:
                button_menu_tree.set_default_selected_item(client.id)

        # Render the menu tree
        return_select = button_menu_tree.render()

        if return_select is not None:
            item = return_select.key
            client = ProjectPlanDTO.get_client_by_id(pmo_table.data, item)
            project = ProjectPlanDTO.get_project_by_id(pmo_table.data, item)
            mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, item)
            if client:
                pmo_state.set_current_client(client)
                pmo_state.set_current_project(None)
                pmo_state.set_current_mission(None)
            elif project:
                client = ProjectPlanDTO.get_client_by_project_id(pmo_table.data, project.id)
                pmo_state.set_current_client(client)
                pmo_state.set_current_project(project)
                pmo_state.set_current_mission(None)
            elif mission:
                project = ProjectPlanDTO.get_project_by_mission_id(pmo_table.data, mission.id)
                client = ProjectPlanDTO.get_client_by_project_id(pmo_table.data, project.id)
                pmo_state.set_current_client(client)
                pmo_state.set_current_project(project)
                pmo_state.set_current_mission(mission)


    # Display the details tab for the current mission
    client = pmo_state.get_current_client()
    project = pmo_state.get_current_project()
    mission = pmo_state.get_current_mission()

    # Right column - Project details
    with right_col:
        if project:
            project_id = project.id
            pmo_state.set_current_project(project)
            # Create a container for the header with project title and action buttons
            header_col1, header_col2 = StreamlitContainers.columns_with_fit_content(
                    key=f"header_project_{project_id}",
                    cols=[1, 'fit-content'], vertical_align_items='center')
            with header_col1:
                st.header(f"{project.name}")
            with header_col2:
                button_project: StreamlitMenuButton = pmo_config.build_project_menu_button(pmo_table, client, project)
                button_project.render()


            if not mission and not project.missions:
                col_message, col_button = st.columns([2, 1])
                with col_message:
                    st.info("This project has no mission yet. Click on the button to add a mission.")
                with col_button:
                    pmo_config.build_new_mission_button(pmo_table, project)

            # Display mission information
            if mission:
                mission_name = mission.mission_name
                mission_id = mission.id
                st.markdown("---")

                header_col1, header_col2, header_col3 = StreamlitContainers.columns_with_fit_content(
                    key=f"header_{mission_id}",
                    cols=[1, 'fit-content', 'fit-content'], vertical_align_items='center')
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

                # Only display if status - progress exists
                status = mission.status
                progress = mission.progress
                status_str = ""
                if status and status != Status.NONE.value:
                    status_str = status
                if progress is not None:
                    if status_str:
                        status_str += " **-** "
                    # Display progress as a percentage
                    status_str += f"{progress}%"
                if status_str:
                    st.markdown(f"**Status:** {status_str}")

                # Only display if priority exists
                priority = mission.priority
                if priority and priority != Priority.NONE.value:
                    st.markdown(f"**Priority:** {priority}")

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
                    cols=[1, 'fit-content'], vertical_align_items='center')
                if not milestones:
                    with title_col:
                        st.info("This project has no milestones yet. Click on the button to add a milestone.")

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
                            vertical_align_items='center',
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
