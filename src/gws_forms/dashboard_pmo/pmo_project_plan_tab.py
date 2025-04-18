import os
import pandas as pd
import streamlit as st
from PIL import Image
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority, Event
from gws_forms.dashboard_pmo._dashboard_code.container.container import st_fixed_container
from gws_forms.dashboard_pmo.streamlit_data_editor import StreamlitDataEditor
from gws_forms.dashboard_pmo.pmo_component import check_if_project_plan_is_edited_sidebar


def display_project_plan_tab(pmo_table: PMOTable):
    """Display the DataFrame in Streamlit tabs."""
    # Define the variable pmo_state
    pmo_state = pmo_table.pmo_state

    # Custom css
    # - to define the size of the scrollbar -> because it was dificult to select the horizontal scrollbar
    # - We added padding: 10px; because otherwise it would create a horizontal scrolling bar in the global window
    # -> with certain screen sizes, this would cause the display to bog down when there were 2 rows in the table, for example.
    st.markdown("""
            <style>
                .dvn-scroller::-webkit-scrollbar {
                width: 5px;
                height: 10px;
                }
                .block-container{
                padding: 10px;
                }

            </style>
    """, unsafe_allow_html=True)

    # Show the dataframe and make it editable
    data = pmo_table.get_filter_df().reset_index()
    # Define column configurations
    column_config = {pmo_table.NAME_COLUMN_START_DATE: st.column_config.DateColumn(
        pmo_table.NAME_COLUMN_START_DATE, format="DD MM YYYY"),
        pmo_table.NAME_COLUMN_END_DATE: st.column_config.DateColumn(
        pmo_table.NAME_COLUMN_END_DATE, format="DD MM YYYY"),
        pmo_table.NAME_COLUMN_STATUS: st.column_config.SelectboxColumn(
        options=[s.value for s in Status]),
        pmo_table.NAME_COLUMN_PRIORITY: st.column_config.SelectboxColumn(
        options=[p.value for p in Priority]),
        pmo_table.NAME_COLUMN_DELETE: st.column_config.CheckboxColumn(default=False), }

    project_plan_edited = st.data_editor(data,
                                         column_order=pmo_table.DEFAULT_COLUMNS_LIST,
                                         use_container_width=True,
                                         hide_index=True,
                                         num_rows=pmo_table.dynamic_df, height=pmo_table.calculate_height(),
                                         column_config=column_config, key="editor")

    # Check if the project plan has been edited
    pmo_table.table_editing_state = not (
        pmo_table.get_filter_df()[pmo_table.DEFAULT_COLUMNS_LIST]
        .copy()
        .reset_index(drop=True)
        .equals(project_plan_edited[pmo_table.DEFAULT_COLUMNS_LIST])
    )

    check_if_project_plan_is_edited_sidebar(pmo_table)

    if pmo_table.choice_project_plan != "Load":
        # Add a template screenshot as an example
        with st.expander('Download the project plan template', icon=":material/help_outline:"):

            # Allow users to download the template
            @st.cache_data
            def convert_df(df: pd.DataFrame) -> pd.DataFrame:
                return df.to_csv().encode('utf-8')
            df_template = pd.read_csv(os.path.join(os.path.abspath(
                os.path.dirname(__file__)), "template.csv"), index_col=False)

            csv = convert_df(df_template)
            st.download_button(
                label="Download Template",
                data=csv,
                file_name='project_template.csv',
                mime='text/csv',
            )

            image = Image.open(os.path.join(os.path.abspath(os.path.dirname(
                __file__)), "example_template_pmo.png"))  # template screenshot provided as an example
            st.image(
                image,  caption='Make sure you use the same column names as in the template')

    pmo_state.get_show_success_project_plan()

    with st_fixed_container(mode="sticky", position="bottom", border=False, transparent=False):
        cols = st.columns([1, 2])
        with cols[0]:
            # if at least there is one True in the column delete, we change the name of the button to inform the user
            # that rows will be deleted
            if project_plan_edited[pmo_table.NAME_COLUMN_DELETE].any():
                name_button = "Delete selected and save"
            else:
                name_button = "Save changes"
            if st.button(name_button, use_container_width=False, icon=":material/save:"):
                streamlit_data_editor = StreamlitDataEditor(dataframe_displayed=project_plan_edited, key="editor")
                pmo_table.commit(streamlit_data_editor)
                # Save dataframe in the folder
                pmo_table.save_df_in_folder()

                # Apply the observer -> Update tag folder
                if pmo_table.observer:
                    check = pmo_table.observer.update(Event(event_type='update_line'))
                    if not check:
                        raise Exception("Something got wrong, close the app and try again.")
                pmo_state.set_show_success_project_plan(True)
                st.rerun()
        with cols[1]:
            if pmo_state.get_show_success_project_plan():
                st.success("Saved!")
    if pmo_state.get_show_success_project_plan():
        pmo_state.set_show_success_project_plan(False)
