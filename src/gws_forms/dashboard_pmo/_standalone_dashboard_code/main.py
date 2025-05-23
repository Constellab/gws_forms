import streamlit as st
import json
from gws_forms.dashboard_pmo.pmo_table import PMOTable
from gws_forms.dashboard_pmo.pmo_dashboard import run
from gws_forms.dashboard_pmo.pmo_dto import ProjectPlanDTO
import os
import tempfile
from gws_core import Folder, Settings

st.title("Standalone PMO Dashboard")

if "data_folder" not in st.session_state:
    data_folder_path = Settings.make_temp_dir()
    data_folder : Folder = Folder(data_folder_path)
    st.session_state["data_folder"] = data_folder
    # create subfolders
    data_folder.create_dir_if_not_exist("Project Plan")
    data_folder.create_dir_if_not_exist("Change Log")
    data_folder.create_dir_if_not_exist("Notes")
    data_folder.create_dir_if_not_exist("Settings")

data_folder_path = st.session_state["data_folder"].path
folder_project_plan = os.path.join(data_folder_path, "Project Plan")
folder_details = os.path.join(data_folder_path, "Notes")
folder_change_log = os.path.join(data_folder_path, "Change Log")
folder_settings = os.path.join(data_folder_path, "Settings")

pmo_table = PMOTable(folder_project_plan=folder_project_plan,
                     folder_details=folder_details, folder_change_log=folder_change_log,
                     folder_settings=folder_settings)

run(pmo_table)

