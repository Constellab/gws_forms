from gws_forms.dashboard_pmo.pmo_table import PMOTable
#Code inspired by this tutorial : https://medium.com/codex/create-a-simple-project-planning-app-using-streamlit-and-gantt-chart-6c6adf8f46dd

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

folder_project_plan = sources[0].path
folder_details = sources[1].path
folder_change_log = sources[2].path

pmoTable = PMOTable(json_path = None, folder_project_plan = folder_project_plan, folder_details= folder_details, folder_change_log = folder_change_log)
pmoTable.display_tabs()