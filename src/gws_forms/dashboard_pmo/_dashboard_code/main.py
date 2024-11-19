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


#Code inspired by this tutorial : https://medium.com/codex/create-a-simple-project-planning-app-using-streamlit-and-gantt-chart-6c6adf8f46dd

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

folder_project_plan = sources[0].path
folder_details = sources[1].path

# Create tabs
tab_project_plan, tab_gantt, tab_plot_overview, tab_details = st.tabs(["Project Plan", "Gantt", "Plot overview", "Details"])

with tab_project_plan :
    #Add a file uploader to allow users to upload their project plan file
    st.subheader('Project plan')
    # List all csv files in the saved directory
    files = sorted([f.split(".csv")[0] for f in os.listdir(folder_project_plan) if f.endswith(".csv")], reverse=True)
    if files :
        choice_project_plan = st.selectbox("Select an option", ["Load" , "Upload", "Fill manually"])
    else :
        choice_project_plan = st.selectbox("Select an option", ["Upload", "Fill manually"])

    project_plan_df = pd.DataFrame(columns = ["Project Name","Mission Name","Mission Referee","Team Members","Start Date","End Date","Milestones","Status","Priority","Progress (%)","Next Steps","Comments","Visibility"])

    #Load data
    if choice_project_plan == "Load":
        # Show a selectbox to choose one file; by default, choose the last one
        selected_file = st.selectbox(label="Choose an existing project plan",
                                        options=files, index=0, placeholder="Select a project plan")
        # Load the selected file and display its contents
        if selected_file:
            selected_file = selected_file + ".csv"
            file_path = os.path.join(folder_project_plan, selected_file)
            project_plan_df = pd.read_csv(file_path)
    #Upload data
    elif choice_project_plan == "Upload":
        uploaded_file = st.file_uploader("Upload your project plan.", type=['csv'], key ="file_uploader")
        if uploaded_file is not None:
            project_plan_df=pd.read_csv(uploaded_file)
        else:
            st.warning('You need to upload a csv file.')
    #Change data type
    project_plan_df['Start Date'] = project_plan_df['Start Date'].fillna('').astype('datetime64[ns]')
    project_plan_df['End Date'] = project_plan_df['End Date'].fillna('').astype('datetime64[ns]')
    project_plan_df['Milestones'] = project_plan_df['Milestones'].fillna('').astype('str')
    project_plan_df['Priority'] = project_plan_df['Priority'].fillna('').astype('str')
    project_plan_df['Progress (%)'] = project_plan_df['Progress (%)'].astype('float')
    project_plan_df['Next Steps'] = project_plan_df['Next Steps'].fillna('').astype('str')
    project_plan_df['Comments'] = project_plan_df['Comments'].fillna('').astype('str')
    project_plan_df['Visibility'] = project_plan_df['Visibility'].fillna('').astype('str')
    project_plan_df['Project Name'] = project_plan_df['Project Name'].fillna('').astype('str')
    project_plan_df['Mission Name'] = project_plan_df['Mission Name'].fillna('').astype('str')
    project_plan_df['Mission Referee'] = project_plan_df['Mission Referee'].fillna('').astype('str')
    project_plan_df['Team Members'] = project_plan_df['Team Members'].fillna('').astype('str')
    #Show the dataframe and make it editable
    edited_project_plan_df = st.data_editor(project_plan_df, use_container_width = True, hide_index=True, num_rows="dynamic", column_config={
            "Start Date": st.column_config.DatetimeColumn("Start Date", format="DD MM YYYY"),
            "End Date": st.column_config.DatetimeColumn("End Date", format="DD MM YYYY"),
            "Status": st.column_config.SelectboxColumn(
            options=[
                "📝 Todo",
                "📈 In progress",
                "✅ Done",
                "☑️ Closed"]),
            "Priority": st.column_config.SelectboxColumn(
            options=[
                "🔴 High",
                "🟡 Medium",
                "🟢 Low"])
            })


    if st.button("Save project plan"):
        #Save dataframe in the folder
        timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"project_plan-%d_%m_%Y-%Hh%M.csv")
        path = os.path.join(folder_project_plan, timestamp)
        edited_project_plan_df.to_csv(path, index = False)
        st.success("Project plan saved, you can find it in the Folder Project Plan")

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

with tab_gantt :
    st.subheader('Generate the Gantt chart')
    #Replace empty strings with No members in the Team members column in order to show it in the Gantt chart
    edited_project_plan_df['Team Members'] = edited_project_plan_df['Team Members'].replace('', None)  # Treat empty strings as None
    edited_project_plan_df['Team Members'] = edited_project_plan_df['Team Members'].fillna('No members')

    gantt_choice = st.selectbox("View Gantt Chart by:", ["Mission Referee","Team Members",'Progress (%)', "Project Name","Mission Name"],index=0)

    fig = px.timeline(
                    edited_project_plan_df,
                    x_start="Start Date",
                    x_end="End Date",
                    y="Project Name",
                    color=gantt_choice,
                    hover_name="Mission Name",
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
        status_counts = edited_project_plan_df['Status'].value_counts()
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
            annotations=[dict(text='Status', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig)

    with cols[1]:
        edited_project_plan_df['Priority'] = edited_project_plan_df['Priority'].replace('', None)  # Treat empty strings as None
        edited_project_plan_df['Priority'] = edited_project_plan_df['Priority'].fillna('NaN')
        # Data for the donut chart
        # Calculate the count of each status
        status_counts = edited_project_plan_df['Priority'].value_counts()
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
            annotations=[dict(text='Priority', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig)

with tab_details :
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
    list_projects = edited_project_plan_df['Project Name'].unique()
    with cols_1[0]:
        project_selected : str = st.selectbox(label = r"$\textbf{\text{\large{Choose a project}}}$", options = list_projects)
    if project_selected :
        list_missions = edited_project_plan_df[edited_project_plan_df['Project Name'] == project_selected]['Mission Name']
        with cols_1[1]:
            mission_selected : str = st.selectbox(label = r"$\textbf{\text{\large{Choose a mission}}}$", options = list_missions)
        if mission_selected :
            # Key for the text data
            key = f"{project_selected}_{mission_selected}"
            # Retrieve existing text if available
            existing_text = st.session_state.text_data.get(key, "")
            # Input area for the text
            text_input = st.text_area(label=r"$\textbf{\text{\large{Details:}}}$",value=existing_text, key=key)

            # Save button
            if st.button("Save Text"):
                # Update session state with the new text
                st.session_state.text_data[key] = text_input

                # Save to JSON file
                timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"details-%d_%m_%Y-%Hh%M.json")
                file_path = os.path.join(folder_details,timestamp)
                with open(file_path, "w") as json_file:
                    json.dump(st.session_state.text_data, json_file, indent=4)

                st.success(f"Text for {project_selected} - {mission_selected} saved successfully!")
