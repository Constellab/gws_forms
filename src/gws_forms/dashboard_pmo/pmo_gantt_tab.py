import io
import streamlit as st
import plotly.express as px
from datetime import datetime
import pandas as pd
from gws_forms.dashboard_pmo.pmo_table import PMOTable


def display_gantt_tab(pmo_table: PMOTable):

    gantt_choice = st.selectbox(
        "View Gantt Chart by:",
        [pmo_table.NAME_COLUMN_MISSION_REFEREE, pmo_table.NAME_COLUMN_TEAM_MEMBERS, pmo_table.NAME_COLUMN_PROGRESS,
         pmo_table.NAME_COLUMN_PROJECT_NAME, pmo_table.NAME_COLUMN_MISSION_NAME],
        index=0)

    # Convert dates to datetime format
    processed_data = pmo_table.processed_data.copy()
    for item in processed_data:
        if item.get(pmo_table.NAME_COLUMN_START_DATE):
            item[pmo_table.NAME_COLUMN_START_DATE] = pd.to_datetime(item[pmo_table.NAME_COLUMN_START_DATE])
        if item.get(pmo_table.NAME_COLUMN_END_DATE):
            item[pmo_table.NAME_COLUMN_END_DATE] = pd.to_datetime(item[pmo_table.NAME_COLUMN_END_DATE])

    fig = px.timeline(
        processed_data,
        x_start=pmo_table.NAME_COLUMN_START_DATE,
        x_end=pmo_table.NAME_COLUMN_END_DATE,
        y=pmo_table.NAME_COLUMN_PROJECT_NAME,
        color=gantt_choice,
        hover_name=pmo_table.NAME_COLUMN_MISSION_NAME,
        color_discrete_sequence=px.colors.qualitative.Pastel,
        color_continuous_scale=px.colors.sequential.algae,
        range_color=(0, 100))

    fig.update_coloraxes(colorbar_title=gantt_choice)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        title='Project Plan Gantt Chart',
        hoverlabel_bgcolor='#DAEEED',
        bargap=0.2, height=600, xaxis_title="", yaxis_title="", title_x=0.5, barmode='group',
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
