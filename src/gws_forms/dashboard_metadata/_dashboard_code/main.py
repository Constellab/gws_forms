from gws_forms.dashboard_metadata.metadata_dashboard import run
from gws_forms.dashboard_metadata.metadata_state import MetadataState

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

folder_metadata = sources[0].path

# Initialize Metadata State
metadata_state = MetadataState(folder_metadata)

run(metadata_state = metadata_state)
