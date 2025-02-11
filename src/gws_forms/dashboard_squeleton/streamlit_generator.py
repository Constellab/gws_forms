
import os

from gws_core import (ConfigParams, OutputSpec, OutputSpecs, StreamlitResource, Task, TaskInputs, TaskOutputs, task_decorator,
                      dashboard_decorator, Dashboard, DashboardType, TypingStyle)

@dashboard_decorator("GenerateDashboardSqueleton", dashboard_type=DashboardType.STREAMLIT)
class GenerateDashboardSqueleton(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_dashboard_code"
        )


@task_decorator("StreamlitSqueletonGenerator", human_name="Squeleton dashboard",
                short_description="Task to generate a squeleton Streamlit dashboard",
                style=TypingStyle.community_icon(icon_technical_name="dashboard",
                                                     background_color="#b57fb4"))
class StreamlitSqueletonGenerator(Task):

    """
    StreamlitSqueletonGenerator is a task that generates a squeleton Streamlit dashboard.


    Output : a Streamlit app.

    """
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()

        # set dashboard reference
        streamlit_resource.set_dashboard(GenerateDashboardSqueleton())

        return {'streamlit_app': streamlit_resource}
