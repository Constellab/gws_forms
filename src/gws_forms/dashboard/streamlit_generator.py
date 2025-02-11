
import os

from gws_core import (ConfigParams, OutputSpec, OutputSpecs, StreamlitResource, Task, TaskInputs, TaskOutputs, task_decorator,InputSpec, InputSpecs,
                      dashboard_decorator, Dashboard, DashboardType, Folder, TypingStyle, JSONDict)

@dashboard_decorator("GenerateDashboardFormsAnswer", dashboard_type=DashboardType.STREAMLIT)
class GenerateDashboardFormsAnswer(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_dashboard_code"
        )

@task_decorator("StreamlitFormsDashbaordGenerator", human_name="Forms dashboard",
                short_description="Task to generate a custom Streamlit dashboard to create form",
                style=TypingStyle.material_icon(material_icon_name="question_answer",
                                                background_color="#413ebb"))
class StreamlitFormsDashbaordGenerator(Task):

    """
    StreamlitFormsDashbaordGenerator is a task that generates a Streamlit dashboard designed to create forms
    based on a provided JSON file containing the questions.

    Input :  a JSONDict file containing the questions.
    Output : a Streamlit app.

    """
    input_specs: InputSpecs = InputSpecs({'questions_file': InputSpec(
        JSONDict, human_name="JSONDict containing the questions")})
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()

        # set the input in the streamlit resource
        questions_file: JSONDict = inputs.get('questions_file')
        streamlit_resource.add_resource(
            questions_file, create_new_resource=False)
        folder_sessions: Folder = Folder(self.create_tmp_dir())
        folder_sessions.name = "Answers"
        streamlit_resource.add_resource(
            folder_sessions, create_new_resource=True)

        # set dashboard reference
        streamlit_resource.set_dashboard(GenerateDashboardFormsAnswer())

        return {'streamlit_app': streamlit_resource}
