
import os

from gws_core import (AppConfig, AppType, ConfigParams, Folder, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      TaskOutputs, TypingStyle, app_decorator, task_decorator)


@app_decorator("GenerateDashboardCreationForms", app_type=AppType.STREAMLIT)
class GenerateDashboardCreationForms(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_dashboard_code"
        )


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

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()

        folder_sessions: Folder = Folder(self.create_tmp_dir())
        folder_sessions.name = "Answers"
        streamlit_resource.add_resource(
            folder_sessions, create_new_resource=True)

        # set dashboard reference
        streamlit_resource.set_app_config(GenerateDashboardCreationForms())

        return {'streamlit_app': streamlit_resource}
