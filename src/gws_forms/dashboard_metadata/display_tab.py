import streamlit as st
import pandas as pd
from gws_forms.dashboard_metadata.metadata_state import MetadataState
from gws_core.streamlit import StreamlitContainers, dataframe_paginated

def render_display_tab(metadata_state : MetadataState):

    # Load the JSON file
    metadata_json = metadata_state.get_metadata_json()

    # Convert to list of dicts
    rows = []
    for item in metadata_json["metadata"]:
        name = item.get("name", "")
        allowed_values = item.get("allowed_values", "")
        description = item.get("description", "")
        response_type = item.get("response_type", "")
        min_value = item.get("min_value", "")
        max_value = item.get("max_value", "")

        rows.append({
            "name": name,
            "description": description,
            "response_type": response_type,
            "valeurs": allowed_values,
            "min_value" : min_value,
            "max_value" : max_value
        })

    # Create DataFrame
    df = pd.DataFrame(rows)

    if df.empty:
        st.warning("Please add some metadata first")
        return

    with StreamlitContainers.full_width_dataframe_container('container-full-dataframe'):
        #TODO : quand il y aura une nouvelle version de gws_core pour pouvoir utiliser use_container_width et hide_index
        """dataframe_paginated(df, use_container_width=True, hide_index = True, paginate_rows=True, row_page_size_options=[25, 50, 100],
            transformer = lambda df: df.style.format(thousands=" ", precision=1), key='row_paginated')"""
        st.dataframe(df, use_container_width=True, hide_index = True)