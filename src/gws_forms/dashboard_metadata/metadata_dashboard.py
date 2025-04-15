
import streamlit as st

from .add_tab import render_add_tab
from .display_tab import render_display_tab

from gws_forms.dashboard_metadata.metadata_state import MetadataState
def show_content(metadata_state : MetadataState):

    def render_add_page():
        render_add_tab(metadata_state=metadata_state)

    def render_display_page():
        render_display_tab(metadata_state=metadata_state)

    add_page = st.Page(render_add_page, title='Add', url_path='add', icon='✏️')
    display_page = st.Page(render_display_page, title='Display', url_path='display', icon='📄')

    pg = st.navigation([add_page, display_page])

    pg.run()


def run(metadata_state : MetadataState):

    show_content(metadata_state)
