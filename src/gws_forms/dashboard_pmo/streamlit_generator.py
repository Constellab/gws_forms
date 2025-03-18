
import os

from gws_core import (ConfigParams, OutputSpec, OutputSpecs, StreamlitResource, Task, TaskInputs, TaskOutputs, task_decorator,
                      dashboard_decorator, Dashboard, DashboardType, Folder, TypingStyle)

@dashboard_decorator("GenerateDashboardPMO", dashboard_type=DashboardType.STREAMLIT)
class GenerateDashboardPMO(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_dashboard_code"
        )

@task_decorator("StreamlitPMOGenerator", human_name="PMO dashboard",
                short_description="Task to generate a PMO Streamlit dashboard",
                style=TypingStyle.community_icon(icon_technical_name="dashboard",
                                                     background_color="#b57fb4"))
class StreamlitPMOGenerator(Task):

    """
    StreamlitPMOGenerator is a task that generates a Project Management Office (PMO) Streamlit dashboard.


    Output : a Streamlit app.

    """
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()

        folder_project_plan: Folder = Folder(self.create_tmp_dir())
        folder_project_plan.name = "Project Plan"
        streamlit_resource.add_resource(
            folder_project_plan, create_new_resource=True)

        folder_details: Folder = Folder(self.create_tmp_dir())
        folder_details.name = "Notes"
        streamlit_resource.add_resource(
            folder_details, create_new_resource=True)

        folder_change_log: Folder = Folder(self.create_tmp_dir())
        folder_change_log.name = "Change Log"
        streamlit_resource.add_resource(
            folder_change_log, create_new_resource=True)


        # set dashboard reference
        streamlit_resource.set_dashboard(GenerateDashboardPMO())

        return {'streamlit_app': streamlit_resource}
