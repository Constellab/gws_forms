import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO, MilestoneDTO
from gws_forms.dashboard_pmo.pmo_config import PMOConfig
from gws_forms.dashboard_pmo.dialog_functions import delete_milestone, add_milestone, edit_milestone
from gws_core.streamlit import StreamlitMenuButton, StreamlitRouter, StreamlitMenuButtonItem, StreamlitContainers, StreamlitHelper
from streamlit_tree_select import tree_select

def update_milestone(pmo_table: PMOTable, key: str, milestone: MilestoneDTO):
    """Update the milestone status when the checkbox is clicked."""
    # Update the milestone status
    pmo_table.update_milestone_status_by_id(milestone.id, st.session_state[key])
    pmo_table.commit_and_save()

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

        # Build nodes from actual data: Client > Project > Mission
        nodes = []

        projects_list = ProjectPlanDTO.get_projects(pmo_table.data)
        # Sort project data by client name
        projects_list.sort(key=lambda x: (
            x.client_name.lower()
        ))

        for project in projects_list:
            # Find if this client already exists in nodes
            client_node = next((n for n in nodes if n["value"] == project.id + "_client"), None)
            if not client_node:
                client_node = {
                    "label": project.client_name,
                    "value": project.id + "_client",  # Use project.id + suffix to ensure uniqueness
                    "children": []
                }
                nodes.append(client_node)
            # Add project node under client
            project_node = {
                "label": project.name,
                "value": project.id,
                "children": []
            }

            # Define status order mapping
            status_order = Status.get_order()

            # Sort project data by status first, then mission name
            project.missions.sort(key=lambda x: (
                status_order.get(x.status),  # Status order
                x.mission_name.lower()  # Mission name alphabetically
            ))

            # Add mission nodes under project
            for mission in project.missions:
                mission_node = {
                    "label": mission.mission_name,
                    "value": mission.id
                }

                project_node["children"].append(mission_node)
            client_node["children"].append(project_node)

        if pmo_state.get_current_mission():
            nodes_already_checked = pmo_state.get_current_mission().id
        elif pmo_state.get_current_project():
            nodes_already_checked = pmo_state.get_current_project().id
        else:
            project = projects_list[0]
            if project.missions:
                nodes_already_checked = project.missions[0].id
            else:
                nodes_already_checked = project.id

        #nodes_already_checked = pmo_state.get_current_mission().id if pmo_state.get_current_mission() else pmo_state.get_current_project().id if pmo_state.get_current_project() else projects_list[0].id
        expanded = [pmo_state.get_current_project().id, pmo_state.get_current_project().id + "_client"] if pmo_state.get_current_project() else [projects_list[0].id, projects_list[0].id + "_client"]
        return_select = tree_select(nodes, checked = [nodes_already_checked],
                                    expanded = expanded, check_model="leaf", expand_on_click = True)#, only_leaf_checkboxes = True)
        #st.write(return_select)#TODO remove
        # It's lean that more than one mission is selected, but we don't want to
        if len(return_select["checked"]) > 1:
            for item in return_select["checked"]:
                # If the item is in expanded, it means it's a project
                if f"{item}_client" in return_select["expanded"]:
                    # The list return_select["checked"] is not filled one click after another
                    # but depending on the hierarchy so we need to find the entry different from the current project (=previous project)
                    if item != pmo_state.get_current_project().id:
                        project = ProjectPlanDTO.get_project_by_id(pmo_table.data, item)
                        pmo_state.set_current_project(project)
                        pmo_state.set_current_mission(project.missions[0] if project.missions else None)
                        st.rerun()
                # The item is a mission
                else:
                    # The list return_select["checked"] is not filled one click after another
                    # but depending on the hierarchy so we need to find the entry different from the current mission (=previous mission)
                    if not pmo_state.get_current_mission():
                        # This case manage when the user had selected a project without mission before and now select a mission
                        mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, item)
                        pmo_state.set_current_mission(mission)
                        project = ProjectPlanDTO.get_project_by_mission_id(pmo_table.data, mission.id)
                        pmo_state.set_current_project(project)
                        st.rerun()

                    elif item != pmo_state.get_current_mission().id:
                        mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, item)
                        pmo_state.set_current_mission(mission)
                        project = ProjectPlanDTO.get_project_by_mission_id(pmo_table.data, mission.id)
                        pmo_state.set_current_project(project)
                        st.rerun()
        elif len(return_select["checked"]) == 1 and return_select["checked"][0] is not None:
            item = return_select["checked"][0]
            if f"{item}_client" in return_select["expanded"]:
                project = ProjectPlanDTO.get_project_by_id(pmo_table.data, item)
                pmo_state.set_current_project(project)
                pmo_state.set_current_mission(None)
            else:
                mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, item)
                pmo_state.set_current_mission(mission)
                project = ProjectPlanDTO.get_project_by_mission_id(pmo_table.data, mission.id)
                pmo_state.set_current_project(project)


    # Display the details tab for the current mission
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
                button_project: StreamlitMenuButton = pmo_config.build_project_menu_button(pmo_table, project)
                button_project.render()


            if not mission :
                col_message, col_button = st.columns([2, 1])
                with col_message:
                    st.info("This project has no mission yet. Click on the button to add a mission.")
                with col_button:
                    pmo_config.build_new_mission_button(pmo_table, project)

            # Display mission information
            else:
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
