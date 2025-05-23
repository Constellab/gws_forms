import os

from gws_core import (
    ConfigParams, InputSpecs, InputSpec, OutputSpec, OutputSpecs, StreamlitResource, Task, TaskInputs, TaskOutputs,
    task_decorator, dashboard_decorator, Dashboard, DashboardType, Folder, TypingStyle)


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
    input_specs: InputSpecs = InputSpecs({'data': InputSpec(Folder, human_name="Folder containing the data")})
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()

        data_folder: Folder = inputs.get('data')

        # Create the 3 required folders if they do not exist
        data_folder.create_dir_if_not_exist("Project Plan")
        data_folder.create_dir_if_not_exist("Change Log")
        data_folder.create_dir_if_not_exist("Notes")
        data_folder.create_dir_if_not_exist("Settings")

        streamlit_resource.add_resource(
            data_folder, create_new_resource=False)

        # set dashboard reference
        streamlit_resource.set_dashboard(GenerateDashboardPMO())

        return {'streamlit_app': streamlit_resource}
