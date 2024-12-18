import json
import os
import io
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import pytz
from gws_forms.e_table.e_table import Etable
from gws_forms.dashboard_pmo._dashboard_code.container.container import st_fixed_container


class PMOTable(Etable):

    #Define columns names
    NAME_COLUMN_START_DATE = 'Start Date'
    NAME_COLUMN_END_DATE = 'End Date'
    NAME_COLUMN_MILESTONES = 'Milestones'
    NAME_COLUMN_PRIORITY = 'Priority'
    NAME_COLUMN_PROGRESS = 'Progress (%)'
    NAME_COLUMN_COMMENTS = 'Comments'
    NAME_COLUMN_VISIBILITY = 'Visibility'
    NAME_COLUMN_PROJECT_NAME = 'Project Name'
    NAME_COLUMN_MISSION_NAME = 'Mission Name'
    NAME_COLUMN_MISSION_REFEREE = 'Mission Referee'
    NAME_COLUMN_TEAM_MEMBERS = 'Team Members'
    NAME_COLUMN_STATUS = "Status"
    DEFAULT_COLUMNS_LIST = [NAME_COLUMN_PROJECT_NAME, NAME_COLUMN_MISSION_NAME,NAME_COLUMN_MISSION_REFEREE,NAME_COLUMN_TEAM_MEMBERS,NAME_COLUMN_START_DATE,NAME_COLUMN_END_DATE,NAME_COLUMN_MILESTONES,NAME_COLUMN_STATUS,NAME_COLUMN_PRIORITY,NAME_COLUMN_PROGRESS,NAME_COLUMN_COMMENTS,NAME_COLUMN_VISIBILITY]
    # Constants for height calculation
    ROW_HEIGHT = 35  # Height per row in pixels
    HEADER_HEIGHT = 38  # Height for the header in pixels

    def __init__(self, json_path = None, folder_project_plan = None, folder_details = None):
        """
        Initialize the PMOTable object with the data file containing the project missions.
        Functions will define the actions to perform with the PMO table in order to see them in the dashboard
        """
        super().__init__(json_path)
        self.folder_project_plan = folder_project_plan
        self.folder_details = folder_details
        self.required_columns = {
            self.NAME_COLUMN_PROJECT_NAME: self.TEXT,
            self.NAME_COLUMN_MISSION_NAME: self.TEXT,
            self.NAME_COLUMN_MISSION_REFEREE: self.TEXT,
            self.NAME_COLUMN_TEAM_MEMBERS: self.TEXT,
            self.NAME_COLUMN_START_DATE: self.DATE,
            self.NAME_COLUMN_END_DATE: self.DATE,
            self.NAME_COLUMN_MILESTONES: self.TEXT,
            self.NAME_COLUMN_STATUS: self.TEXT,
            self.NAME_COLUMN_PRIORITY: self.TEXT,
            self.NAME_COLUMN_PROGRESS: self.NUMERIC,
            self.NAME_COLUMN_COMMENTS: self.TEXT,
            self.NAME_COLUMN_VISIBILITY: self.TEXT
        }

        self.df = self.validate_columns(self.df)
        self.project_plan_df = self.df.copy()

        self.tab_widgets = {
            # Base tab widget
            "Table": self.display_project_plan_tab,
            "Gantt" : self.display_gantt_tab,
            "Plot overview" : self.display_plot_overview_tab,
            "Details" : self.display_details_tab,
            "Todo" : self.display_todo_tab
        }
        self.edition = True
        self.choice_project_plan = None
        self.original_project_plan_df = None


    # Function to calculate progress
    def calculate_progress(self,row):
        if row[self.NAME_COLUMN_MILESTONES] == "nan" or pd.isna(row[self.NAME_COLUMN_MILESTONES]):
            return 0
        # Count the number of steps (total "-"" and "✅")
        total_steps = row[self.NAME_COLUMN_MILESTONES].count("-") + row[self.NAME_COLUMN_MILESTONES].count("✅")
        # Count the number of completed steps (✅ only)
        completed_steps = row[self.NAME_COLUMN_MILESTONES].count("✅")
        # Calculate the progress as a percentage
        if total_steps > 0:
            return (completed_steps / total_steps) * 100
        else:
            return 0


    def validate_columns(self, df):
        """Ensures the required columns are present and have the correct types."""
        for column, col_type in self.required_columns.items():
            if column not in df.columns:
                df[column] = None
            if col_type == self.DATE:
                df[column] = df[column].fillna('').astype('datetime64[ns]')
            elif col_type == self.TEXT:
                df[column] = df[column].astype(str)
            elif col_type == self.NUMERIC:
                df[column] = df[column].astype(float)

        #Replace empty strings with No members in the Team members column in order to show it in the Gantt chart TODO : trouver un moyen que quand le df est modifié alors ça fait bien les changements suivants aussi
        df[self.NAME_COLUMN_TEAM_MEMBERS] = df[self.NAME_COLUMN_TEAM_MEMBERS].replace('', None)  # Treat empty strings as None
        df[self.NAME_COLUMN_TEAM_MEMBERS] = df[self.NAME_COLUMN_TEAM_MEMBERS].fillna('No members')
        df[self.NAME_COLUMN_PRIORITY] = df[self.NAME_COLUMN_PRIORITY].replace('', 'nan')
        df[self.NAME_COLUMN_PRIORITY] = df[self.NAME_COLUMN_PRIORITY].replace('None', 'nan')
        df[self.NAME_COLUMN_STATUS] = df[self.NAME_COLUMN_STATUS].replace('', 'nan')
        df[self.NAME_COLUMN_STATUS] = df[self.NAME_COLUMN_STATUS].replace('None', 'nan')
        # Replace empty strings in the milestones column with None
        df[self.NAME_COLUMN_MILESTONES] = df[self.NAME_COLUMN_MILESTONES].replace('', np.nan)
        df[self.NAME_COLUMN_MILESTONES] = df[self.NAME_COLUMN_MILESTONES].replace('None', np.nan)
        # Convert None to pd.NaT
        df[self.NAME_COLUMN_START_DATE] = df[self.NAME_COLUMN_START_DATE].apply(lambda x: pd.NaT if x is None else x)

        # Apply the function to calculate progress
        df[self.NAME_COLUMN_PROGRESS] = df.apply(self.calculate_progress, axis=1)

        return df

    def display_tabs(self):
        if "df_to_save" not in st.session_state:
            st.session_state.df_to_save = PMOTable().df
        self.display_sidebar()
        names = list(self.tab_widgets.keys())
        widgets = list(self.tab_widgets.values())
        st_tabs = st.tabs(names)
        for idx, st_tab in enumerate(st_tabs):
            with st_tab:
                widgets[idx]()


    def dataframe_modified(self):
        with st.sidebar :
            if not self.original_project_plan_df.equals(self.df):
                st.error("Save your project plan before filtering/sorting", icon="🚨")

    def calculate_height(self):
        #Define the height of the dataframe : 100 rows to show or the number of max rows
        if len(self.project_plan_df) < 100:
            return self.ROW_HEIGHT*(len(self.project_plan_df.reset_index(drop=True))+1) + self.HEADER_HEIGHT
        else :
            return self.HEADER_HEIGHT + self.ROW_HEIGHT * 100

    def display_sidebar(self):
        if "df_to_save" not in st.session_state:
            st.session_state.df_to_save = PMOTable().df

        with st.sidebar :
            st.write("**Load files**")
            with st.expander('Project plan file',icon=":material/description:"):
                # List all csv files in the saved directory
                files = sorted([f.split(".csv")[0] for f in os.listdir(self.folder_project_plan) if f.endswith(".csv")], reverse=True)
                cols = st.columns(2)
                if files :
                    with cols[0]:
                        self.choice_project_plan = st.selectbox("Select an option", ["Load" , "Upload", "Fill manually"], key = "choice_project_plan")
                else :
                    with cols[0]:
                        self.choice_project_plan = st.selectbox("Select an option", ["Upload", "Fill manually"], key = "choice_project_plan_sidebar")

                #Load data
                if self.choice_project_plan == "Load":
                    with cols[1]:
                        # Show a selectbox to choose one file; by default, choose the last one
                        selected_file = st.selectbox(label="Choose an existing project plan",
                                                        options=files, index=0, placeholder="Select a project plan", key = "selected_file_sidebar")
                        # Load the selected file and display its contents
                        if selected_file:
                            selected_file = selected_file + ".csv"
                            file_path = os.path.join(self.folder_project_plan, selected_file)
                            self.project_plan_df = pd.read_csv(file_path)
                            self.project_plan_df = self.validate_columns(self.project_plan_df)
                #Upload data
                #Add a file uploader to allow users to upload their project plan file
                elif self.choice_project_plan == "Upload":
                    with cols[1]:
                        uploaded_file = st.file_uploader("Upload your project plan.", type=['csv'], key ="file_uploader_sidebar")
                        if uploaded_file is not None:
                            self.project_plan_df=pd.read_csv(uploaded_file)
                        else:
                            st.warning('You need to upload a csv file.')

            with st.expander('Details file',icon=":material/description:"):
                cols = st.columns(2)
                # List all json files in the saved directory
                files = sorted([f.split(".json")[0] for f in os.listdir(self.folder_details) if f.endswith(".json")], reverse=True)
                if files :
                    with cols[0]:
                        choice_details = st.selectbox("Select an option", ["Load" , "New"])
                else:
                    choice_details = "New"

                if choice_details == "New":
                    # Create a dictionary to store text data
                    if "text_data" not in st.session_state:
                        st.session_state.text_data = {}

                elif choice_details == "Load":
                    with cols[1]:
                        # Show a selectbox to choose one file; by default, choose the last one
                        selected_file = st.selectbox(label="Select an existing detail file", options=files, index=0, placeholder="Select a detail")
                        # Load the selected file and display its contents
                        if selected_file:
                            selected_file = selected_file + ".json"
                            file_path = os.path.join(self.folder_details, selected_file)
                            if os.path.exists(file_path):
                                with open(file_path, "r", encoding="utf-8") as f:
                                    st.session_state.text_data = json.load(f)

        self.original_project_plan_df = self.project_plan_df.copy()

        with st.sidebar:
            st.write("**Filtering/Sortering**")
            #Sortering
            with st.expander('Sort',icon=":material/swap_vert:"):
                selected_column_order : str = st.selectbox(label="Select the column to sort", options=self.project_plan_df.columns, index=0, placeholder="Select a column")
                selected_order = st.selectbox(label="Sort ...", options=["in alphabetical order", "in non-alphabetical order"], index=None, placeholder="Select a sort")
            if selected_order == "in alphabetical order" :
                self.project_plan_df = self.project_plan_df.sort_values(by=selected_column_order).reset_index(drop=True)
            elif selected_order == "in non-alphabetical order" :
                self.project_plan_df = self.project_plan_df.sort_values(by=selected_column_order, ascending=False).reset_index(drop=True)
            #Filtering
            with st.expander('Filter',icon=":material/filter_alt:"):
                selected_regex_filter_project_name = st.text_input(label = PMOTable.NAME_COLUMN_PROJECT_NAME, placeholder = PMOTable.NAME_COLUMN_PROJECT_NAME)
                selected_regex_filter_mission_name = st.text_input(label = PMOTable.NAME_COLUMN_MISSION_NAME, placeholder = PMOTable.NAME_COLUMN_MISSION_NAME)
                selected_mission_referee : str = st.selectbox(label=PMOTable.NAME_COLUMN_MISSION_REFEREE, options=self.project_plan_df[PMOTable.NAME_COLUMN_MISSION_REFEREE].unique(), index=None, placeholder=PMOTable.NAME_COLUMN_MISSION_REFEREE)
                selected_regex_filter_team_members = st.text_input(label = PMOTable.NAME_COLUMN_TEAM_MEMBERS, placeholder = PMOTable.NAME_COLUMN_TEAM_MEMBERS)
                selected_status : str = st.selectbox(label=PMOTable.NAME_COLUMN_STATUS, options=self.project_plan_df[PMOTable.NAME_COLUMN_STATUS].unique(), index=None, placeholder=PMOTable.NAME_COLUMN_STATUS)
                selected_priority : str = st.selectbox(label=PMOTable.NAME_COLUMN_PRIORITY, options=self.project_plan_df[PMOTable.NAME_COLUMN_PRIORITY].unique(), index=None, placeholder=PMOTable.NAME_COLUMN_PRIORITY)
            if selected_regex_filter_project_name :
                self.project_plan_df = self.project_plan_df[self.project_plan_df[PMOTable.NAME_COLUMN_PROJECT_NAME].str.contains(selected_regex_filter_project_name, case=False)]
                self.edition = False
            if selected_regex_filter_mission_name :
                self.project_plan_df = self.project_plan_df[self.project_plan_df[PMOTable.NAME_COLUMN_MISSION_NAME].str.contains(selected_regex_filter_mission_name, case=False)]
                self.edition = False
            if selected_mission_referee is not None :
                self.project_plan_df = self.project_plan_df.loc[self.project_plan_df[PMOTable.NAME_COLUMN_MISSION_REFEREE].isin([selected_mission_referee])]
                self.edition = False
            if selected_regex_filter_team_members :
                self.project_plan_df = self.project_plan_df[self.project_plan_df[PMOTable.NAME_COLUMN_TEAM_MEMBERS].str.contains(selected_regex_filter_team_members, case=False)]
                self.edition = False
            if selected_status is not None :
                self.project_plan_df = self.project_plan_df.loc[self.project_plan_df[PMOTable.NAME_COLUMN_STATUS].isin([selected_status])]
                self.edition = False
            if selected_priority is not None :
                self.project_plan_df = self.project_plan_df.loc[self.project_plan_df[PMOTable.NAME_COLUMN_PRIORITY].isin([selected_priority])]
                self.edition = False


    def display_project_plan_tab(self):
        """Display the DataFrame in Streamlit tabs."""
        if "df_to_save" not in st.session_state:
            st.session_state.df_to_save = PMOTable().df

        if self.edition is True :
            #Show the dataframe and make it editable
            self.df = st.data_editor(self.project_plan_df, use_container_width = True, hide_index=True, num_rows="dynamic", on_change = self.dataframe_modified,height=self.calculate_height(),
                column_config={
                self.NAME_COLUMN_START_DATE: st.column_config.DateColumn(self.NAME_COLUMN_START_DATE, format="DD MM YYYY"),
                self.NAME_COLUMN_END_DATE: st.column_config.DateColumn(self.NAME_COLUMN_END_DATE, format="DD MM YYYY"),
                self.NAME_COLUMN_STATUS: st.column_config.SelectboxColumn(
                options=[
                    "📝 Todo",
                    "📈 In progress",
                    "✅ Done",
                    "☑️ Closed"]),
                self.NAME_COLUMN_PRIORITY: st.column_config.SelectboxColumn(
                options=[
                    "🔴 High",
                    "🟡 Medium",
                    "🟢 Low"])
                })
            st.session_state["df_to_save"] = self.df
        else :
            st.session_state["df_to_save"] = self.original_project_plan_df
            self.df = self.project_plan_df
            st.dataframe(self.df)


        if self.choice_project_plan != "Load":
            #Add a template screenshot as an example
            with st.expander('Download the project plan template',icon=":material/help_outline:"):

                #Allow users to download the template
                @st.cache_data
                def convert_df(df):
                    return df.to_csv().encode('utf-8')
                df_template = pd.read_csv(os.path.join(os.path.abspath(os.path.dirname(__file__)), "template.csv"), index_col = False)

                csv = convert_df(df_template)
                st.download_button(
                    label="Download Template",
                    data=csv,
                    file_name='project_template.csv',
                    mime='text/csv',
                )

                image = Image.open(os.path.join(os.path.abspath(os.path.dirname(__file__)),"example_template_pmo.png")) #template screenshot provided as an example
                st.image(image,  caption='Make sure you use the same column names as in the template')

        with st_fixed_container(mode="sticky", position="bottom", border=False, transparent = False):
            cols = st.columns([1,2])
            with cols[0]:
                if st.button("Save changes", use_container_width=False, icon = ":material/save:"):
                    st.session_state["df_to_save"] = self.validate_columns(st.session_state["df_to_save"])
                    self.df = self.validate_columns(self.df)
                    #Save dataframe in the folder
                    timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"plan_%Y-%m-%d-%Hh%M")
                    path_csv = os.path.join(self.folder_project_plan, f"{timestamp}.csv")
                    path_json = os.path.join(self.folder_project_plan, f"{timestamp}.json")
                    st.session_state["df_to_save"].to_csv(path_csv, index = False)

                    with open(path_json, 'w', encoding='utf-8') as f:
                        json.dump(st.session_state["df_to_save"].to_json(orient="records", indent=2), f, ensure_ascii=False, indent=4)

                    with cols[1]:
                        st.success("Saved ! You can find it in the Folder Project Plan")


    def display_gantt_tab(self):
        if "df_to_save" not in st.session_state:
            st.session_state.df_to_save = PMOTable().df
        self.df = self.validate_columns(self.df)
        gantt_choice = st.selectbox("View Gantt Chart by:", [self.NAME_COLUMN_MISSION_REFEREE,self.NAME_COLUMN_TEAM_MEMBERS,self.NAME_COLUMN_PROGRESS, self.NAME_COLUMN_PROJECT_NAME, self.NAME_COLUMN_MISSION_NAME],index=0)

        fig = px.timeline(
                        self.df,
                        x_start=self.NAME_COLUMN_START_DATE,
                        x_end= self.NAME_COLUMN_END_DATE,
                        y= self.NAME_COLUMN_PROJECT_NAME,
                        color=gantt_choice,
                        hover_name= self.NAME_COLUMN_MISSION_NAME,
                        color_discrete_sequence=px.colors.qualitative.Pastel,
                        color_continuous_scale=px.colors.sequential.algae,
                        range_color=(0, 100))

        fig.update_coloraxes(colorbar_title= gantt_choice)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
                        title='Project Plan Gantt Chart',
                        hoverlabel_bgcolor='#DAEEED',
                        bargap=0.2,height=600,xaxis_title="",yaxis_title="",title_x=0.5,barmode='group',
                        xaxis=dict(
                                tickfont_size=15,
                                tickangle = 270,
                                rangeslider_visible=True,
                                side ="top",
                                showgrid = True,
                                zeroline = True,
                                showline = True,
                                showticklabels = True,
                                tickformat="%d %m %Y",
                                )
                    )

        fig.update_xaxes(tickangle=0, tickfont=dict(family='Poppins', color='black', size=13))

        st.plotly_chart(fig, use_container_width=True)

        #Export to HTML
        buffer = io.StringIO()
        fig.write_html(buffer, include_plotlyjs='cdn')
        html_bytes = buffer.getvalue().encode()
        st.download_button(
            label='Export to HTML',
            data=html_bytes,
            file_name='Gantt.html',
            mime='text/html'
        )

    def display_plot_overview_tab(self):
        if "df_to_save" not in st.session_state:
            st.session_state.df_to_save = PMOTable().df
        self.df = self.validate_columns(self.df)
        cols = st.columns(2)

        with cols[0]:
            # Data for the donut chart
            # Calculate the count of each status
            status_counts = self.df[self.NAME_COLUMN_STATUS].value_counts()
            labels = status_counts.index.tolist()
            values = status_counts.values.tolist()

            colors = ["#3f78e0", "#8cb2ff", "#ff9e4a", "#ff4c4c"]

            # Create the donut chart
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.5,  # Creates the donut hole effect
                marker=dict(colors=colors),
                textinfo='percent+label',  # Show both percent and label
                insidetextorientation='radial'
            )])

            # Customize layout
            fig.update_layout(
                title_text="Overall Task Status",
                annotations=[dict(text=self.NAME_COLUMN_STATUS, x=0.5, y=0.5, font_size=20, showarrow=False)]
            )

            # Display the chart in Streamlit
            st.plotly_chart(fig)

        with cols[1]:
            # Data for the donut chart
            # Filter rows where the column has values different from None
            non_none_values = self.df[self.NAME_COLUMN_PRIORITY].notna()

            # Perform value_counts only on non-None values
            if non_none_values.any():
                # Calculate the count of each status
                status_counts = self.df[self.NAME_COLUMN_PRIORITY].value_counts()
                labels = status_counts.index.tolist()
                values = status_counts.values.tolist()

                # Colors for each section
                status_colors = {
                    "🔴 High": "#ff4c4c",
                    "🟡 Medium": "#f2eb1d",
                    "🟢 Low": "#59d95e",
                    "nan": "#abaa93"
                }
                colors = [status_colors[status] for status in labels]

                # Create the donut chart
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.5,  # Creates the donut hole effect
                    marker=dict(colors=colors),
                    textinfo='percent+label',  # Show both percent and label
                    insidetextorientation='radial'
                )])

                # Customize layout
                fig.update_layout(
                    title_text="Overall Task Priority",
                    annotations=[dict(text=self.NAME_COLUMN_PRIORITY, x=0.5, y=0.5, font_size=20, showarrow=False)]
                )

                # Display the chart in Streamlit
                st.plotly_chart(fig)

    def display_details_tab(self):
        if "df_to_save" not in st.session_state:
            st.session_state.df_to_save = PMOTable().df
        self.df = self.validate_columns(self.df)

        cols_1 = st.columns(2)
        list_projects = self.df[self.NAME_COLUMN_PROJECT_NAME].unique()
        if len(list_projects)>0 :
            with cols_1[0]:
                project_selected : str = st.selectbox(label = r"$\textbf{\text{\large{Choose a project}}}$", options = list_projects)
            if project_selected :
                list_missions = self.df[self.df[self.NAME_COLUMN_PROJECT_NAME] == project_selected][self.NAME_COLUMN_MISSION_NAME]
                with cols_1[1]:
                    mission_selected : str = st.selectbox(label = r"$\textbf{\text{\large{Choose a mission}}}$", options = list_missions)
                if mission_selected :
                    # Key for the text data
                    key = f"{project_selected}_{mission_selected}"
                    # Retrieve existing text if available
                    existing_text = st.session_state.text_data.get(key, "")
                    # Input area for the text
                    text_input = st.text_area(label=r"$\textbf{\text{\large{Details:}}}$",value=existing_text, key=key)

                    with st_fixed_container(mode="sticky", position="bottom", border=False, transparent = False):
                        # Save button
                        if st.button("Save Text", icon = ":material/save:"):
                            # Update session state with the new text
                            st.session_state.text_data[key] = text_input

                            # Save to JSON file
                            timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"details_%Y-%m-%d-%Hh%M.json")
                            file_path = os.path.join(self.folder_details,timestamp)
                            with open(file_path, "w", encoding="utf-8") as json_file:
                                json.dump(st.session_state.text_data, json_file, indent=4, encoding="utf-8")

                            st.success(f"Text for {project_selected} - {mission_selected} saved successfully!")
        else :
            st.warning(f"Please complete the {self.NAME_COLUMN_PROJECT_NAME} column first")

    def display_todo_tab(self):
        if "df_to_save" not in st.session_state:
            st.session_state.df_to_save = PMOTable().df
        self.df = self.validate_columns(self.df)

        # Filter the relevant columns
        filtered_df = self.df[[self.NAME_COLUMN_PROJECT_NAME, self.NAME_COLUMN_MISSION_NAME, self.NAME_COLUMN_MILESTONES]]
        updated_milestones = {}
        if not filtered_df.empty :
            # Group by project name
            grouped_by_project = filtered_df.groupby(self.NAME_COLUMN_PROJECT_NAME)

            # Iterate through each project
            number_project = 0
            for project_name, group in grouped_by_project:
                if (group[self.NAME_COLUMN_MILESTONES] != "nan").any():
                    st.subheader(f"**Project:** {project_name}")
                    number_mission =0
                    # Iterate through missions within the project
                    for index, row in group.iterrows():
                        mission_name = row[self.NAME_COLUMN_MISSION_NAME]
                        milestones = row[self.NAME_COLUMN_MILESTONES]
                        if milestones != "nan":
                            # Split milestones into individual tasks
                            task_list = milestones.split("\n")

                            # Display mission name before the tasks
                            st.write(f"**Mission:** {mission_name}")

                            updated_task_list = []
                            number_task = 0
                            for task in task_list:
                                # Check if the task is marked as completed
                                is_completed = task.startswith("✅")
                                if self.edition == True :
                                    if is_completed :
                                        checked_task = st.checkbox(label = f"~~{task}~~", key = f"{project_name}_{mission_name}_{task}_{number_project}_{number_mission}_{number_task}", value = is_completed)
                                    else :
                                        checked_task = st.checkbox(label = task, key = f"{project_name}_{mission_name}_{task}_{number_project}_{number_mission}_{number_task}", value = is_completed)

                                    # Update the task's status
                                    if checked_task:
                                        task = f"✅{task[1:]}" if task.startswith("-") else task
                                    else:
                                        task = f"-{task[1:]}" if task.startswith("✅") else task

                                    updated_task_list.append(task)
                                    number_task += 1
                                else:
                                    st.write(task)

                            # Store updated tasks back in the milestones for this mission
                            updated_milestones[index] = "\n".join(updated_task_list)
                        else:
                            updated_milestones[index] = ""
                        number_mission +=1
                number_project +=1

            if self.edition == True :
                if "show_success_todo" not in st.session_state:
                    st.session_state["show_success_todo"] = False
                with st_fixed_container(mode="sticky", position="bottom", border=False, transparent = False):
                    cols = st.columns([1,2])
                    with cols[0]:
                        if st.button("Update infos", use_container_width=False, icon = ":material/save:"):
                            # Apply the updates to the original DataFrame
                            for index, new_milestones in updated_milestones.items():
                                self.df.at[index, self.NAME_COLUMN_MILESTONES] = new_milestones

                            # Save updated DataFrame to session state
                            st.session_state["df_to_save"] = self.df
                            #Save dataframe in the folder
                            timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"plan_%Y-%m-%d-%Hh%M.csv")
                            path = os.path.join(self.folder_project_plan, timestamp)
                            st.session_state["df_to_save"].to_csv(path, index = False)
                            st.session_state["show_success_todo"] = True
                            st.rerun()
                    with cols[1]:
                        if st.session_state["show_success_todo"]:
                            st.success("Changes saved!")

                if st.session_state["show_success_todo"]:
                    st.session_state["show_success_todo"] = False
        else :
            st.warning(f"Please complete the {self.NAME_COLUMN_MILESTONES} column first")
