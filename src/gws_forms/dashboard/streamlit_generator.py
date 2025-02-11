
import os

from gws_core import (BoolParam, ConfigParams, ConfigSpecs, Dashboard,
                      DashboardType, Folder, InputSpec, InputSpecs, JSONDict,
                      OutputSpec, OutputSpecs, StreamlitResource, StrParam,
                      Task, TaskInputs, TaskOutputs, TypingStyle,
                      dashboard_decorator, task_decorator)


@dashboard_decorator("GenerateFormsDashboard", dashboard_type=DashboardType.STREAMLIT)
class GenerateFormsDashboard(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_form_dashboard_code"
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
        'streamlit_form_app': OutputSpec(StreamlitResource, human_name="Streamlit Form app")
    })
    config_specs: ConfigSpecs = {
        'logo':
        StrParam(
            human_name="Form logo",
            short_description="Url of the logo that will be printed next to the form title",
            optional=False),
        'title': StrParam(
            human_name="Title",
            short_description="Title of the form",
            optional=False),
        'results_visible':
        BoolParam(
            human_name="Results visible",
            short_description="If True, users will be able to see all results of the forms",
            default_value=True)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        folder_sessions: Folder = Folder(self.create_tmp_dir())
        folder_sessions.name = "Answers"

        # build the streamlit form app resource with the code and the resources
        streamlit_resource = StreamlitResource()

        # set the input in the streamlit resource
        questions_file: JSONDict = inputs.get('questions_file')
        streamlit_resource.add_resource(
            questions_file, create_new_resource=False)
        streamlit_resource.add_resource(
            folder_sessions, create_new_resource=True)
        streamlit_resource.set_params(params)
        # set the app folder
        streamlit_resource.set_dashboard(GenerateFormsDashboard())

        # build the streamlit responses app resource with the code and the resources
        return {'streamlit_form_app': streamlit_resource}
