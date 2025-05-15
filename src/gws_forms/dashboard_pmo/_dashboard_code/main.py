from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_dashboard import run

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

folder_project_plan = sources[0].path
folder_details = sources[1].path
folder_change_log = sources[2].path

pmo_table = PMOTable(folder_project_plan=folder_project_plan,
                     folder_details=folder_details, folder_change_log=folder_change_log)

run(pmo_table)
