import os
import io
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from  PIL import Image
import pytz

#Code inspired by this tutorial : https://medium.com/codex/create-a-simple-project-planning-app-using-streamlit-and-gantt-chart-6c6adf8f46dd

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

folder_project_plan = sources[0].path

# Streamlit app title
col1, col2 = st.columns([1,10])
logo_gencovery_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logo/logo_gencovery.png")
with col1:
    st.image(logo_gencovery_path,  width=100)
with col2 :
    # Add the CSS for styling
    st.markdown("""<style>
        .font {
            font-size:30px;
            font-family: 'Poppins', sans-serif;
            color: #2DBDB4;}</style>""", unsafe_allow_html=True)
    # Use markdown to display the title with the custom class
    st.markdown('<p class="font">PMO Dashboard</p>', unsafe_allow_html=True)

# Create tabs
tab_project_plan, tab_gantt = st.tabs(["Project Plan", "Gantt"])

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
                "☑️ Closed"])
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

        image = Image.open(os.path.join(os.path.abspath(os.path.dirname(__file__)),"example_template.png")) #template screenshot provided as an example
        st.image(image,  caption='Make sure you use the same column names as in the template')

with tab_gantt :
    st.subheader('Generate the Gantt chart')

    gantt_choice = st.selectbox("View Gantt Chart by:", ["Mission Referee","Team Members",'Progress (%)', "Project Name","Mission Name"],index=0)

    fig = px.timeline(
                    edited_project_plan_df,
                    x_start="Start Date",
                    x_end="End Date",
                    y="Project Name",
                    color=gantt_choice,
                    hover_name="Mission Name",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                    )

    fig.update_yaxes(autorange="reversed")

    fig.update_layout(
                    title='Project Plan Gantt Chart',
                    hoverlabel_bgcolor='#DAEEED',
                    bargap=0.2,height=600,xaxis_title="",yaxis_title="",title_x=0.5,
                    xaxis=dict(
                            tickfont_size=15,
                            tickangle = 270,
                            rangeslider_visible=True,
                            side ="top",
                            showgrid = True,
                            zeroline = True,
                            showline = True,
                            showticklabels = True,
                            tickformat="%x\n",
                            )
                )

    fig.update_xaxes(tickangle=0, tickfont=dict(family='Rockwell', color='blue', size=15))

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
