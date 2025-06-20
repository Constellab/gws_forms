import io
import streamlit as st
import plotly.express as px
import pandas as pd
from gws_forms.dashboard_pmo.pmo_table import PMOTable

# Code inspired by this tutorial : https://medium.com/codex/create-a-simple-project-planning-app-using-streamlit-and-gantt-chart-6c6adf8f46dd


def display_gantt_tab(pmo_table: PMOTable):

    gantt_choice = st.selectbox(
        "View Gantt Chart by:",
        [pmo_table.NAME_COLUMN_MISSION_REFEREE, pmo_table.NAME_COLUMN_TEAM_MEMBERS, pmo_table.NAME_COLUMN_PROGRESS,
        pmo_table.NAME_COLUMN_CLIENT_NAME,pmo_table.NAME_COLUMN_PROJECT_NAME, pmo_table.NAME_COLUMN_MISSION_NAME],
        index=0)

    # Prepare data for Gantt chart
    gantt_data = []
    for client in pmo_table.data.data:
        for project in client.projects:
            for mission in project.missions:
                gantt_data.append({
                    pmo_table.NAME_COLUMN_CLIENT_NAME: client.client_name,
                    pmo_table.NAME_COLUMN_PROJECT_NAME: client.client_name+"_"+project.name,
                    pmo_table.NAME_COLUMN_MISSION_NAME: mission.mission_name,
                    pmo_table.NAME_COLUMN_START_DATE: mission.start_date,
                    pmo_table.NAME_COLUMN_END_DATE: mission.end_date,
                    pmo_table.NAME_COLUMN_MISSION_REFEREE: mission.mission_referee,
                    pmo_table.NAME_COLUMN_TEAM_MEMBERS: ", ".join(mission.team_members) if mission.team_members else "",
                    pmo_table.NAME_COLUMN_PROGRESS: mission.progress,
                    pmo_table.NAME_COLUMN_PRIORITY: mission.priority,
                    pmo_table.NAME_COLUMN_STATUS: mission.status
                })

    # Convert to DataFrame
    df = pd.DataFrame(gantt_data)

    # Ensure date columns are in datetime format
    df[pmo_table.NAME_COLUMN_START_DATE] = pd.to_datetime(df[pmo_table.NAME_COLUMN_START_DATE], errors='coerce')
    df[pmo_table.NAME_COLUMN_END_DATE] = pd.to_datetime(df[pmo_table.NAME_COLUMN_END_DATE], errors='coerce')

    # Create Gantt chart
    fig = px.timeline(
        df,
        x_start=pmo_table.NAME_COLUMN_START_DATE,
        x_end=pmo_table.NAME_COLUMN_END_DATE,
        y=pmo_table.NAME_COLUMN_PROJECT_NAME,
        color=gantt_choice,  # Use the column name directly
        hover_name=pmo_table.NAME_COLUMN_MISSION_NAME,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title = " ",
        range_x=[df[pmo_table.NAME_COLUMN_START_DATE].min(), df[pmo_table.NAME_COLUMN_END_DATE].max()],
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        hoverlabel_bgcolor='#DAEEED',
        bargap=0.2,
        height=600,
        xaxis_title="Timeline",
        yaxis_title="Projects",
        title_x=0.5,
        barmode='group',
        margin=dict(l=60, r=60, t=60, b=60),  # <-- Added margin here
        xaxis=dict(
            tickfont_size=15,
            tickangle=270,
            rangeslider_visible=True,
            side="top",
            showgrid=True,
            zeroline=True,
            showline=True,
            showticklabels=True,
            tickformat="%d %m %Y",
        )
    )

    fig.update_xaxes(tickangle=0, tickfont=dict(
        family='Poppins', color='black', size=13))

    st.plotly_chart(fig, use_container_width=True)

    # Export to HTML
    buffer = io.StringIO()
    fig.write_html(buffer, include_plotlyjs='cdn')
    html_bytes = buffer.getvalue().encode()
    st.download_button(
        label='Export to HTML',
        data=html_bytes,
        file_name='Gantt.html',
        mime='text/html'
    )
