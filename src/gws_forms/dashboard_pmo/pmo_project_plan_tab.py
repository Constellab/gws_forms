import streamlit as st
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO, MilestoneDTO
from gws_forms.dashboard_pmo.pmo_config import PMOConfig
from gws_forms.dashboard_pmo.dialog_functions import delete_milestone,  add_milestone, edit_milestone
from gws_core.streamlit import StreamlitMenuButton, StreamlitRouter, StreamlitMenuButtonItem, StreamlitContainers, StreamlitHelper
from st_aggrid import AgGrid
from streamlit_slickgrid import (
    add_tree_info,
    slickgrid,
    Formatters,
    Filters,
    FieldType,
    OperatorType,
    ExportServices,
    StreamlitSlickGridFormatters,
    StreamlitSlickGridSorters,
)



def display_project_plan_tab(pmo_table: PMOTable):
    router = StreamlitRouter.load_from_session()

    pmo_config = PMOConfig.get_instance()
    left_col, right_col = st.columns([1, 4])
    with left_col:
        # Button to create a new project
        pmo_config.build_new_client_button(pmo_table)

    projects_data = []
    for client in pmo_table.data.data:
        client_name = client.client_name
        if client.projects:
            for project in client.projects:
                project_name = project.name
                if project.missions:
                    for mission in project.missions:
                        mission_name = mission.mission_name
                        # Convert dates to string for JSON serialization
                        start_date = mission.start_date.isoformat() if hasattr(mission.start_date, "isoformat") else str(mission.start_date) if mission.start_date else ""
                        end_date = mission.end_date.isoformat() if hasattr(mission.end_date, "isoformat") else str(mission.end_date) if mission.end_date else ""
                        projects_data.append({
                            "id": mission.id,
                            pmo_table.NAME_COLUMN_CLIENT_NAME: client_name,
                            pmo_table.NAME_COLUMN_PROJECT_NAME: project_name,
                            pmo_table.NAME_COLUMN_MISSION_NAME: mission_name,
                            pmo_table.NAME_COLUMN_MISSION_REFEREE: mission.mission_referee,
                            pmo_table.NAME_COLUMN_TEAM_MEMBERS: ", ".join(mission.team_members) if mission.team_members else "",
                            pmo_table.NAME_COLUMN_START_DATE: start_date,
                            pmo_table.NAME_COLUMN_END_DATE: end_date,
                            pmo_table.NAME_COLUMN_STATUS: mission.status,
                            pmo_table.NAME_COLUMN_PRIORITY: mission.priority,
                            pmo_table.NAME_COLUMN_PROGRESS: mission.progress,
                            pmo_table.NAME_COLUMN_MILESTONES: ", ".join([m.name for m in mission.milestones]) if mission.milestones else "",
                        })
                else:
                    # Provide a placeholder for mission name
                    projects_data.append({
                        "id": project.id,
                        pmo_table.NAME_COLUMN_CLIENT_NAME: client_name,
                        pmo_table.NAME_COLUMN_PROJECT_NAME: project_name,
                        pmo_table.NAME_COLUMN_MISSION_NAME: "",
                        pmo_table.NAME_COLUMN_MISSION_REFEREE: "",
                        pmo_table.NAME_COLUMN_TEAM_MEMBERS: "",
                        pmo_table.NAME_COLUMN_START_DATE: "",
                        pmo_table.NAME_COLUMN_END_DATE: "",
                        pmo_table.NAME_COLUMN_STATUS: "",
                        pmo_table.NAME_COLUMN_PRIORITY: "",
                        pmo_table.NAME_COLUMN_PROGRESS: "",
                        pmo_table.NAME_COLUMN_MILESTONES: "",
                    })
        else:
            # Provide a placeholder for project and mission name
            projects_data.append({
                "id": client.id,
                pmo_table.NAME_COLUMN_CLIENT_NAME: client_name,
                pmo_table.NAME_COLUMN_PROJECT_NAME: "",
                pmo_table.NAME_COLUMN_MISSION_NAME: "",
                pmo_table.NAME_COLUMN_MISSION_REFEREE: "",
                pmo_table.NAME_COLUMN_TEAM_MEMBERS: "",
                pmo_table.NAME_COLUMN_START_DATE: "",
                pmo_table.NAME_COLUMN_END_DATE: "",
                pmo_table.NAME_COLUMN_STATUS: "",
                pmo_table.NAME_COLUMN_PRIORITY: "",
                pmo_table.NAME_COLUMN_PROGRESS: "",
                pmo_table.NAME_COLUMN_MILESTONES: "",
            })


    if projects_data:

        # Some nice colors to use in the table.
        red = "#ff4b4b"
        green = "#21c354"
        white = "#fafafa"

        columns = [
                {
                    "id": pmo_table.NAME_COLUMN_CLIENT_NAME,
                    "name": pmo_table.NAME_COLUMN_CLIENT_NAME,
                    "field": pmo_table.NAME_COLUMN_CLIENT_NAME,
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                },
                {
                    "id": pmo_table.NAME_COLUMN_PROJECT_NAME,
                    "name": pmo_table.NAME_COLUMN_PROJECT_NAME,
                    "field": pmo_table.NAME_COLUMN_PROJECT_NAME,
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                },
                {
                    "id": pmo_table.NAME_COLUMN_MISSION_NAME,
                    "name": pmo_table.NAME_COLUMN_MISSION_NAME,
                    "field": pmo_table.NAME_COLUMN_MISSION_NAME,
                    "sortable": True,
                    "type": FieldType.string,
                    "filterable": True,
                },
                {
                    "id": pmo_table.NAME_COLUMN_MISSION_REFEREE,
                    "name": pmo_table.NAME_COLUMN_MISSION_REFEREE,
                    "field": pmo_table.NAME_COLUMN_MISSION_REFEREE,
                    "sortable": True,
                    "minWidth": 50,
                    "type": FieldType.string,
                    "filterable": True,
                },
                {
                    "id": pmo_table.NAME_COLUMN_START_DATE,
                    "name": pmo_table.NAME_COLUMN_START_DATE,
                    "field": pmo_table.NAME_COLUMN_START_DATE,
                    "type": FieldType.date,
                    "filterable": True,
                    "filter": {"model": Filters.compoundDate},
                    "formatter": Formatters.dateIso,
                },
                {
                    "id": pmo_table.NAME_COLUMN_END_DATE,
                    "name": pmo_table.NAME_COLUMN_END_DATE,
                    "field": pmo_table.NAME_COLUMN_END_DATE,
                    "type": FieldType.date,
                    "filterable": True,
                    "filter": {"model": Filters.compoundDate},
                    "formatter": Formatters.dateIso,
                },
                {
                    "id": pmo_table.NAME_COLUMN_STATUS,
                    "name": pmo_table.NAME_COLUMN_STATUS,
                    "field": pmo_table.NAME_COLUMN_STATUS,
                    "sortable": True,
                    "filterable": True,
                },
                {
                    "id": pmo_table.NAME_COLUMN_PRIORITY,
                    "name": pmo_table.NAME_COLUMN_PRIORITY,
                    "field": pmo_table.NAME_COLUMN_PRIORITY,
                    "sortable": True,
                    "filterable": True,
                },
                {
                    "id": pmo_table.NAME_COLUMN_PROGRESS,
                    "name": pmo_table.NAME_COLUMN_PROGRESS,
                    "field": pmo_table.NAME_COLUMN_PROGRESS,
                    "sortable": True,
                    "minWidth": 100,
                    "type": FieldType.number,
                    "filterable": True,
                    "formatter": StreamlitSlickGridFormatters.barFormatter,
                    "params": {
                        "colors": [[50, white, red], [100, white, green]],
                        "minDecimal": 0,
                        "maxDecimal": 2,
                        "numberSuffix": "%",
                    },
                },

            ]
        """{
            "id": pmo_table.NAME_COLUMN_TEAM_MEMBERS,
            "name": pmo_table.NAME_COLUMN_TEAM_MEMBERS,
            "field": pmo_table.NAME_COLUMN_TEAM_MEMBERS,
            "sortable": True,
            "minWidth": 50,
            "type": FieldType.string,
            "filterable": True,
            },
            {
                "id": pmo_table.NAME_COLUMN_MILESTONES,
                "name": pmo_table.NAME_COLUMN_MILESTONES,
                "field": pmo_table.NAME_COLUMN_MILESTONES,
                "sortable": True,
                "filterable": True,
            }"""

        options = {
            "enableFiltering": True,
            # Set up export options.
            "enableTextExport": True,
            "enableExcelExport": True,
            "enableColumnPicker": True,
            "excelExportOptions": {"sanitizeDataExport": True},
            "textExportOptions": {"sanitizeDataExport": True},
            "externalResources": [
                ExportServices.ExcelExportService,
                ExportServices.TextExportService,
            ],

            # Pin rows.
            "frozenRow": 0,
            "autoResize": {
                "minHeight": 500,
            },
        }
        out = slickgrid(projects_data, columns=columns, options=options, key="mygrid", on_click="rerun")
        if out is not None:
            row, col = out
            # if the id refer to a mission, we need to find the project and mission and client
            mission = ProjectPlanDTO.get_mission_by_id(pmo_table.data, row)
            # if the id refer to a project, we need to find the project and client
            project = ProjectPlanDTO.get_project_by_id(pmo_table.data, row)
            client = ProjectPlanDTO.get_client_by_id(pmo_table.data, row)
            if mission:
                project = ProjectPlanDTO.get_project_by_mission_id(pmo_table.data,row)
                client = ProjectPlanDTO.get_client_by_project_id(pmo_table.data, project.id)
            elif project:
                mission = None
                client = ProjectPlanDTO.get_client_by_project_id(pmo_table.data, project.id)
            elif client :
                project = None
                mission = None

            pmo_table.pmo_state.set_current_project(project)
            pmo_table.pmo_state.set_current_client(client)
            pmo_table.pmo_state.set_current_mission(mission)
            router.navigate('mission')


    else:
        st.info("No projects or missions to display.")
