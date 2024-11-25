import os
import io
import json
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from  PIL import Image
import pytz
from container.container import st_fixed_container

#Code inspired by this tutorial : https://medium.com/codex/create-a-simple-project-planning-app-using-streamlit-and-gantt-chart-6c6adf8f46dd

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

folder_project_plan = sources[0].path
folder_details = sources[1].path

#Define columns names
NAME_COLUMN_START_DATE = 'Start Date'
NAME_COLUMN_END_DATE = 'End Date'
NAME_COLUMN_MILESTONES = 'Milestones'
NAME_COLUMN_PRIORITY = 'Priority'
NAME_COLUMN_PROGRESS = 'Progress (%)'
NAME_COLUMN_NEXT_STEPS = 'Next Steps'
NAME_COLUMN_COMMENTS = 'Comments'
NAME_COLUMN_VISIBILITY = 'Visibility'
NAME_COLUMN_PROJECT_NAME = 'Project Name'
NAME_COLUMN_MISSION_NAME = 'Mission Name'
NAME_COLUMN_MISSION_REFEREE = 'Mission Referee'
NAME_COLUMN_TEAM_MEMBERS = 'Team Members'
NAME_COLUMN_STATUS = "Status"

# Create tabs
tab_project_plan, tab_gantt, tab_plot_overview, tab_details = st.tabs(["Project Plan", "Gantt", "Plot overview", "Details"])

with tab_project_plan :
    with st.sidebar :
        st.write("**Project plan**")
        with st.expander('Project plan file',icon=":material/description:"):
            # List all csv files in the saved directory
            files = sorted([f.split(".csv")[0] for f in os.listdir(folder_project_plan) if f.endswith(".csv")], reverse=True)
            cols = st.columns(2)
            if files :
                with cols[0]:
                    choice_project_plan = st.selectbox("Select an option", ["Load" , "Upload", "Fill manually"])
            else :
                with cols[0]:
                    choice_project_plan = st.selectbox("Select an option", ["Upload", "Fill manually"])

            project_plan_df = pd.DataFrame(columns = [NAME_COLUMN_PROJECT_NAME, NAME_COLUMN_MISSION_NAME,NAME_COLUMN_MISSION_REFEREE,NAME_COLUMN_TEAM_MEMBERS,NAME_COLUMN_START_DATE,NAME_COLUMN_END_DATE,NAME_COLUMN_MILESTONES,NAME_COLUMN_STATUS,NAME_COLUMN_PRIORITY,NAME_COLUMN_PROGRESS,NAME_COLUMN_NEXT_STEPS,NAME_COLUMN_COMMENTS,NAME_COLUMN_VISIBILITY])

            #Load data
            if choice_project_plan == "Load":
                with cols[1]:
                    # Show a selectbox to choose one file; by default, choose the last one
                    selected_file = st.selectbox(label="Choose an existing project plan",
                                                    options=files, index=0, placeholder="Select a project plan")
                    # Load the selected file and display its contents
                    if selected_file:
                        selected_file = selected_file + ".csv"
                        file_path = os.path.join(folder_project_plan, selected_file)
                        project_plan_df = pd.read_csv(file_path)
            #Upload data
            #Add a file uploader to allow users to upload their project plan file
            elif choice_project_plan == "Upload":
                with cols[1]:
                    uploaded_file = st.file_uploader("Upload your project plan.", type=['csv'], key ="file_uploader")
                    if uploaded_file is not None:
                        project_plan_df=pd.read_csv(uploaded_file)
                    else:
                        st.warning('You need to upload a csv file.')
    #Change data type
    project_plan_df[NAME_COLUMN_START_DATE] = project_plan_df[NAME_COLUMN_START_DATE].fillna('').astype('datetime64[ns]')
    project_plan_df[NAME_COLUMN_END_DATE] = project_plan_df[NAME_COLUMN_END_DATE].fillna('').astype('datetime64[ns]')
    project_plan_df[NAME_COLUMN_MILESTONES] = project_plan_df[NAME_COLUMN_MILESTONES].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_PRIORITY] = project_plan_df[NAME_COLUMN_PRIORITY].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_PROGRESS] = project_plan_df[NAME_COLUMN_PROGRESS].astype('float')
    project_plan_df[NAME_COLUMN_NEXT_STEPS] = project_plan_df[NAME_COLUMN_NEXT_STEPS].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_COMMENTS] = project_plan_df[NAME_COLUMN_COMMENTS].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_VISIBILITY] = project_plan_df[NAME_COLUMN_VISIBILITY].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_PROJECT_NAME] = project_plan_df[NAME_COLUMN_PROJECT_NAME].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_MISSION_NAME] = project_plan_df[NAME_COLUMN_MISSION_NAME].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_MISSION_REFEREE] = project_plan_df[NAME_COLUMN_MISSION_REFEREE].fillna('').astype('str')
    project_plan_df[NAME_COLUMN_TEAM_MEMBERS] = project_plan_df[NAME_COLUMN_TEAM_MEMBERS].fillna('').astype('str')

    original_project_plan_df = project_plan_df.copy()

    def dataframe_modified():
        with st.sidebar :
            if not original_project_plan_df.equals(edited_project_plan_df):
                st.error("Save your project plan before filtering/sorting", icon="🚨")

    with st.sidebar:
        #Sortering
        with st.expander('Sort',icon=":material/swap_vert:"):
            selected_column_order : str = st.selectbox(label="Select the column to sort", options=project_plan_df.columns, index=0, placeholder="Select a column")
            selected_order = st.selectbox(label="Sort ...", options=["in alphabetical order", "in non-alphabetical order"], index=None, placeholder="Select a sort")
        if selected_order == "in alphabetical order" :
            project_plan_df = project_plan_df.sort_values(by=selected_column_order).reset_index(drop=True)
        elif selected_order == "in non-alphabetical order" :
            project_plan_df = project_plan_df.sort_values(by=selected_column_order, ascending=False).reset_index(drop=True)
        #Filtering
        with st.expander('Filter',icon=":material/filter_alt:"):
            selected_regex_filter_project_name = st.text_input(label = NAME_COLUMN_PROJECT_NAME, placeholder = NAME_COLUMN_PROJECT_NAME)
            selected_regex_filter_mission_name = st.text_input(label = NAME_COLUMN_MISSION_NAME, placeholder = NAME_COLUMN_MISSION_NAME)
            selected_mission_referee : str = st.selectbox(label=NAME_COLUMN_MISSION_REFEREE, options=project_plan_df[NAME_COLUMN_MISSION_REFEREE].unique(), index=None, placeholder=NAME_COLUMN_MISSION_REFEREE)
            selected_regex_filter_team_members = st.text_input(label = NAME_COLUMN_TEAM_MEMBERS, placeholder = NAME_COLUMN_TEAM_MEMBERS)
            selected_status : str = st.selectbox(label=NAME_COLUMN_STATUS, options=project_plan_df[NAME_COLUMN_STATUS].unique(), index=None, placeholder=NAME_COLUMN_STATUS)
            selected_priority : str = st.selectbox(label=NAME_COLUMN_PRIORITY, options=project_plan_df[NAME_COLUMN_PRIORITY].unique(), index=None, placeholder=NAME_COLUMN_PRIORITY)
        if selected_regex_filter_project_name :
            project_plan_df = project_plan_df[project_plan_df[NAME_COLUMN_PROJECT_NAME].str.contains(selected_regex_filter_project_name, case=False)]
        if selected_regex_filter_mission_name :
            project_plan_df = project_plan_df[project_plan_df[NAME_COLUMN_MISSION_NAME].str.contains(selected_regex_filter_mission_name, case=False)]
        if selected_mission_referee != None :
            project_plan_df = project_plan_df.loc[project_plan_df[NAME_COLUMN_MISSION_REFEREE].isin([selected_mission_referee])]
        if selected_regex_filter_team_members :
            project_plan_df = project_plan_df[project_plan_df[NAME_COLUMN_TEAM_MEMBERS].str.contains(selected_regex_filter_team_members, case=False)]
        if selected_status != None :
            project_plan_df = project_plan_df.loc[project_plan_df[NAME_COLUMN_STATUS].isin([selected_status])]
        if selected_priority != None :
            project_plan_df = project_plan_df.loc[project_plan_df[NAME_COLUMN_PRIORITY].isin([selected_priority])]


    # Constants for height calculation
    ROW_HEIGHT = 35  # Height per row in pixels
    HEADER_HEIGHT = 38  # Height for the header in pixels
    # Calculate the height of the data editor
    def calculate_height():
        #Define the height of the dataframe : 100 rows to show or the number of max rows
        if len(project_plan_df) < 100:
            return ROW_HEIGHT*(len(project_plan_df.reset_index(drop=True))+1)+HEADER_HEIGHT
        else :
            return HEADER_HEIGHT + ROW_HEIGHT *100

    #Show the dataframe and make it editable
    edited_project_plan_df = st.data_editor(project_plan_df, use_container_width = True, hide_index=True, num_rows="dynamic", on_change= dataframe_modified,height=calculate_height(project_plan_df), column_config={
            NAME_COLUMN_START_DATE: st.column_config.DatetimeColumn(NAME_COLUMN_START_DATE, format="DD MM YYYY"),
            NAME_COLUMN_END_DATE: st.column_config.DatetimeColumn(NAME_COLUMN_END_DATE, format="DD MM YYYY"),
            NAME_COLUMN_STATUS: st.column_config.SelectboxColumn(
            options=[
                "📝 Todo",
                "📈 In progress",
                "✅ Done",
                "☑️ Closed"]),
            NAME_COLUMN_PRIORITY: st.column_config.SelectboxColumn(
            options=[
                "🔴 High",
                "🟡 Medium",
                "🟢 Low"])
            })


    if choice_project_plan != "Load":
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
            if st.button("Save project plan", use_container_width=False):
                #Save dataframe in the folder
                timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"plan_%Y-%m-%d-%Hh%M.csv")
                path = os.path.join(folder_project_plan, timestamp)
                original_project_plan_df.to_csv(path, index = False)
                with cols[1]:
                    st.success("Saved ! You can find it in the Folder Project Plan")


with tab_gantt :
    #Replace empty strings with No members in the Team members column in order to show it in the Gantt chart
    edited_project_plan_df[NAME_COLUMN_TEAM_MEMBERS] = edited_project_plan_df[NAME_COLUMN_TEAM_MEMBERS].replace('', None)  # Treat empty strings as None
    edited_project_plan_df[NAME_COLUMN_TEAM_MEMBERS] = edited_project_plan_df[NAME_COLUMN_TEAM_MEMBERS].fillna('No members')

    gantt_choice = st.selectbox("View Gantt Chart by:", [NAME_COLUMN_MISSION_REFEREE,NAME_COLUMN_TEAM_MEMBERS,NAME_COLUMN_PROGRESS, NAME_COLUMN_PROJECT_NAME,NAME_COLUMN_MISSION_NAME],index=0)

    fig = px.timeline(
                    edited_project_plan_df,
                    x_start=NAME_COLUMN_START_DATE,
                    x_end=NAME_COLUMN_END_DATE,
                    y=NAME_COLUMN_PROJECT_NAME,
                    color=gantt_choice,
                    hover_name=NAME_COLUMN_MISSION_NAME,
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

with tab_plot_overview :
    cols = st.columns(2)

    with cols[0]:
        # Data for the donut chart
        # Calculate the count of each status
        status_counts = edited_project_plan_df[NAME_COLUMN_STATUS].value_counts()
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
            annotations=[dict(text=NAME_COLUMN_STATUS, x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig)

    with cols[1]:
        edited_project_plan_df[NAME_COLUMN_PRIORITY] = edited_project_plan_df[NAME_COLUMN_PRIORITY].replace('', None)  # Treat empty strings as None
        edited_project_plan_df[NAME_COLUMN_PRIORITY] = edited_project_plan_df[NAME_COLUMN_PRIORITY].fillna('NaN')
        # Data for the donut chart
        # Calculate the count of each status
        status_counts = edited_project_plan_df[NAME_COLUMN_PRIORITY].value_counts()
        labels = status_counts.index.tolist()
        values = status_counts.values.tolist()

        # Colors for each section
        status_colors = {
            "🔴 High": "#ff4c4c",
            "🟡 Medium": "#f2eb1d",
            "🟢 Low": "#59d95e",
            "NaN": "#abaa93"
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
            annotations=[dict(text=NAME_COLUMN_PRIORITY, x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig)

with tab_details :
    with st.sidebar :
        st.write("**Details**")
        with st.expander('Project plan file',icon=":material/description:"):
            cols = st.columns(2)
            # List all json files in the saved directory
            files = sorted([f.split(".json")[0] for f in os.listdir(folder_details) if f.endswith(".json")], reverse=True)
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
                        file_path = os.path.join(folder_details, selected_file)
                        if os.path.exists(file_path):
                            with open(file_path, "r") as f:
                                st.session_state.text_data = json.load(f)

    cols_1 = st.columns(2)
    list_projects = edited_project_plan_df[NAME_COLUMN_PROJECT_NAME].unique()
    with cols_1[0]:
        project_selected : str = st.selectbox(label = r"$\textbf{\text{\large{Choose a project}}}$", options = list_projects)
    if project_selected :
        list_missions = edited_project_plan_df[edited_project_plan_df[NAME_COLUMN_PROJECT_NAME] == project_selected][NAME_COLUMN_MISSION_NAME]
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
                if st.button("Save Text"):
                    # Update session state with the new text
                    st.session_state.text_data[key] = text_input

                    # Save to JSON file
                    timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"details_%Y-%m-%d-%Hh%M.json")
                    file_path = os.path.join(folder_details,timestamp)
                    with open(file_path, "w") as json_file:
                        json.dump(st.session_state.text_data, json_file, indent=4)

                    st.success(f"Text for {project_selected} - {mission_selected} saved successfully!")

