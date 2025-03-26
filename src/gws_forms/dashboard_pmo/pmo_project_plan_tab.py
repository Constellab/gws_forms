import os
import json
from datetime import datetime
import pytz
import pandas as pd
import streamlit as st
from PIL import Image
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Status, Priority, Event
from gws_forms.dashboard_pmo._dashboard_code.container.container import st_fixed_container

def display_project_plan_tab(pmo_table : PMOTable):
    """Display the DataFrame in Streamlit tabs."""

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

    pmo_table.pmo_state.get_df_to_save()
    pmo_table.pmo_state.get_active_project_plan(pmo_table.df)

    if pmo_table.edition is True:
        active_plan = pmo_table.pmo_state.get_active_project_plan()
        active_plan.Active = True
        pmo_table.pmo_state.set_active_project_plan(active_plan)

    pmo_table.pmo_state.set_df_to_save(pmo_table.pmo_state.get_active_project_plan().copy())
    # Show the dataframe and make it editable
    pmo_table.df = st.data_editor(pmo_table.pmo_state.active_project_plan(pmo_table.df, pmo_table.NAME_COLUMN_ACTIVE).reset_index(),
                                                                column_order=pmo_table.DEFAULT_COLUMNS_LIST, use_container_width=True, hide_index=True, key="editor",
                                                                num_rows=pmo_table.dynamic_df, height=pmo_table.calculate_height(),
                                column_config={
        pmo_table.NAME_COLUMN_START_DATE: st.column_config.DateColumn(pmo_table.NAME_COLUMN_START_DATE, format="DD MM YYYY"),
        pmo_table.NAME_COLUMN_END_DATE: st.column_config.DateColumn(pmo_table.NAME_COLUMN_END_DATE, format="DD MM YYYY"),
        pmo_table.NAME_COLUMN_STATUS: st.column_config.SelectboxColumn(
            options=[
                Status.TODO.value,
                Status.IN_PROGRESS.value,
                Status.DONE.value,
                Status.CLOSED.value]),
        pmo_table.NAME_COLUMN_PRIORITY: st.column_config.SelectboxColumn(
            options=[
                Priority.HIGH.value,
                Priority.MEDIUM.value,
                Priority.LOW.value]),
        pmo_table.NAME_COLUMN_DELETE: st.column_config.CheckboxColumn(default=False)
    })
    if not (
        pmo_table.pmo_state.active_project_plan(pmo_table.df, pmo_table.NAME_COLUMN_ACTIVE)
        [pmo_table.DEFAULT_COLUMNS_LIST].copy().reset_index(drop=True)
        .equals(pmo_table.df[pmo_table.DEFAULT_COLUMNS_LIST])
    ):
        with st.sidebar:
            pmo_table.placeholder_warning_filtering.error(
                "Save your project plan before filtering.", icon="🚨")

    if pmo_table.choice_project_plan != "Load":
        # Add a template screenshot as an example
        with st.expander('Download the project plan template', icon=":material/help_outline:"):

            # Allow users to download the template
            @st.cache_data
            def convert_df(df : pd.DataFrame) -> pd.DataFrame:
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

    pmo_table.pmo_state.get_show_success_project_plan()

    with st_fixed_container(mode="sticky", position="bottom", border=False, transparent=False):
        cols = st.columns([1, 2])
        with cols[0]:
            #if at least there is one True in the column delete, we change the name of the button to inform the user
            # that rows will be deleted
            if pmo_table.df[pmo_table.NAME_COLUMN_DELETE].any():
                name_button = "Delete selected and save"
            else:
                name_button = "Save changes"
            if st.button(name_button, use_container_width=False, icon=":material/save:"):
                pmo_table.df = pmo_table.fill_na_df(pmo_table.df)
                pmo_table.track_and_log_status(old_df=pmo_table.pmo_state.active_project_plan(pmo_table.df, pmo_table.NAME_COLUMN_ACTIVE), new_df=pmo_table.df)
                pmo_table.commit()
                pmo_table.df = pmo_table.validate_columns(pmo_table.df)
                pmo_table.pmo_state.set_active_project_plan(pmo_table.validate_columns(
                    pmo_table.pmo_state.get_active_project_plan()))
                pmo_table.pmo_state.set_df_to_save(pmo_table.pmo_state.get_active_project_plan().copy())
                # Save dataframe in the folder
                timestamp = datetime.now(tz=pytz.timezone(
                    'Europe/Paris')).strftime("plan_%Y-%m-%d-%Hh%M")
                path_csv = os.path.join(
                    pmo_table.folder_project_plan, f"{timestamp}.csv")
                path_json = os.path.join(
                    pmo_table.folder_project_plan, f"{timestamp}.json")
                pmo_table.pmo_state.get_df_to_save().to_csv(
                    path_csv, index=False)

                with open(path_json, 'w', encoding='utf-8') as f:
                    json.dump(pmo_table.pmo_state.get_df_to_save().to_json(
                        orient="records", indent=2), f, ensure_ascii=False, indent=4)

                # Apply the observer -> Update tag folder
                if pmo_table.observer :
                    check = pmo_table.observer.update(Event(event_type='update_line'))
                    if not check:
                        raise Exception ("Something got wrong, close the app and try again.")
                pmo_table.pmo_state.set_show_success_project_plan(True)
                st.rerun()
        with cols[1]:
            if pmo_table.pmo_state.get_show_success_project_plan():
                st.success("Saved!")
    if pmo_table.pmo_state.get_show_success_project_plan():
        pmo_table.pmo_state.set_show_success_project_plan(False)
