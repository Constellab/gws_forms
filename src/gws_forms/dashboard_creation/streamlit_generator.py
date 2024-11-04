
import os

from gws_core import (ConfigParams, InputSpec, InputSpecs,
                      OutputSpec, OutputSpecs, Task, TaskInputs, TaskOutputs, task_decorator, JSONDict, TypingStyle, Folder)
from gws_core.streamlit.streamlit_resource import StreamlitResource


@task_decorator("StreamlitCreationFormsGenerator", human_name="Forms creation dashboard",
                short_description="Task to generate a custom Streamlit dashboard to create form",
                style=TypingStyle.material_icon(material_icon_name="question_answer",
                                                background_color="#413ebb"))
class StreamlitCreationFormsGenerator(Task):

    """
    StreamlitCreationFormsGenerator is a task that generates a Streamlit dashboard designed to create forms.


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

        folder_sessions: Folder = Folder(self.create_tmp_dir())
        folder_sessions.name = "Answers"
        streamlit_resource.add_resource(
            folder_sessions, create_new_resource=True)

        # set the app folder
        streamlit_resource.set_streamlit_folder(self.streamlit_app_folder)

        return {'streamlit_app': streamlit_resource}
