import streamlit as st
import plotly.graph_objects as go
from collections import Counter
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Priority


def display_plot_overview_tab(pmo_table: PMOTable):

    cols = st.columns(2)
    with cols[0]:
        # Data for the donut chart
        # Calculate the count of each status using Counter
        status_counts = Counter(item[pmo_table.NAME_COLUMN_STATUS]
                                for item in pmo_table.processed_data)

        labels = list(status_counts.keys())
        values = list(status_counts.values())

        colors = ["#3f78e0", "#8cb2ff", "#ff9e4a", "#ff4c4c", "#ffcf40"]

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
            annotations=[dict(text=pmo_table.NAME_COLUMN_STATUS,
                              x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig)

    with cols[1]:
        # Data for the donut chart
        # Filter and count priorities
        priority_counts = Counter(
            item[pmo_table.NAME_COLUMN_PRIORITY]
            for item in pmo_table.processed_data
            if item.get(pmo_table.NAME_COLUMN_PRIORITY) is not None
        )

        if priority_counts:
            labels = list(priority_counts.keys())
            values = list(priority_counts.values())

            # Colors for each section
            status_colors = Priority.get_colors()
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
                annotations=[dict(
                    text=pmo_table.NAME_COLUMN_PRIORITY, x=0.5, y=0.5, font_size=20, showarrow=False)]
            )

            # Display the chart in Streamlit
            st.plotly_chart(fig)
