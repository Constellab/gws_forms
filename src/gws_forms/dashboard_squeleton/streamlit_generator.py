
import os

from gws_core import (ConfigParams, OutputSpec, OutputSpecs, Task, TaskInputs, TaskOutputs, task_decorator, TypingStyle, Folder)
from gws_core.streamlit.streamlit_resource import StreamlitResource

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

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    streamlit_app_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "_dashboard_code"
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()

        # set the app folder
        streamlit_resource.set_streamlit_folder(self.streamlit_app_folder)

        return {'streamlit_app': streamlit_resource}
