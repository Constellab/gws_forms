
import os

from gws_core import (AppConfig, AppType, ConfigParams, Folder, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      TaskOutputs, TypingStyle, app_decorator, task_decorator)


@app_decorator("GenerateDashboardMetadata", dashboard_type=AppType.STREAMLIT)
class GenerateDashboardMetadata(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_dashboard_code"
        )

@task_decorator("StreamlitMetadataGenerator", human_name="Metadata dashboard",
                short_description="Task to generate a Metadata Streamlit dashboard",
                style=TypingStyle.community_icon(icon_technical_name="database_2",
                                                     background_color="#b57fb4"))
class StreamlitMetadataGenerator(Task):

    """
    StreamlitMetadataGenerator is a task that generates a dashboard to fill the metadata of a company.


    Output : a Streamlit app.

    """
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()

        folder_metadata: Folder = Folder(self.create_tmp_dir())
        folder_metadata.name = "Metadata"
        streamlit_resource.add_resource(
            folder_metadata, create_new_resource=True)

        # set dashboard reference
        streamlit_resource.set_app_config(GenerateDashboardMetadata())

        return {'streamlit_app': streamlit_resource}
