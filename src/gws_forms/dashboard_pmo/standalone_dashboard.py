import os

from gws_core import (AppConfig, AppType, ConfigParams, Folder, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      TaskOutputs, TypingStyle, app_decorator, task_decorator)


@app_decorator("PMOStandaloneDashboard", dashboard_type=AppType.STREAMLIT)
class PMOStandaloneDashboardClass(AppConfig):

    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_standalone_dashboard_code"
        )

@task_decorator("PMOStandaloneDashboard",
                human_name="Standalone PMO dashboard)",
                short_description="Standalone Streamlit dashboard for PMO",
                style=TypingStyle.community_icon(icon_technical_name="dashboard", background_color="#b57fb4"))
class PMOStandaloneDashboard(Task):
    """
    Standalone PMO dashboard. No data is stored.
    """

    output_specs: OutputSpecs = OutputSpecs(
        {'streamlit_app': OutputSpec(StreamlitResource, human_name="Standalone PMO dashboard")}
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        streamlit_resource = StreamlitResource()
        streamlit_resource.set_app_config(PMOStandaloneDashboardClass())

        streamlit_resource.set_requires_authentication(False)
        return {'streamlit_app': streamlit_resource}
