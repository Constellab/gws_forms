import streamlit as st
import plotly.graph_objects as go
from gws_forms.dashboard_pmo.pmo_table import PMOTable, Priority

def display_plot_overview_tab(pmo_table : PMOTable):
    pmo_table.pmo_state.get_df_to_save()
    pmo_table.pmo_state.get_active_project_plan(pmo_table.df)

    if not (
        pmo_table.pmo_state.active_project_plan(pmo_table.df, pmo_table.NAME_COLUMN_ACTIVE)
        [pmo_table.DEFAULT_COLUMNS_LIST].copy().reset_index(drop=True)
        .equals(pmo_table.df[pmo_table.DEFAULT_COLUMNS_LIST])
    ):
        st.warning("Please save your project plan first")
        return
    pmo_table.df = pmo_table.validate_columns(pmo_table.df)
    cols = st.columns(2)

    with cols[0]:
        # Data for the donut chart
        # Calculate the count of each status
        status_counts = pmo_table.df[pmo_table.NAME_COLUMN_STATUS].value_counts()
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
            annotations=[dict(text=pmo_table.NAME_COLUMN_STATUS,
                                x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig)

    with cols[1]:
        # Data for the donut chart
        # Filter rows where the column has values different from None
        non_none_values = pmo_table.df[pmo_table.NAME_COLUMN_PRIORITY].notna()

        # Perform value_counts only on non-None values
        if non_none_values.any():
            # Calculate the count of each status
            status_counts = pmo_table.df[pmo_table.NAME_COLUMN_PRIORITY].value_counts(
            )
            labels = status_counts.index.tolist()
            values = status_counts.values.tolist()

            # Colors for each section
            status_colors = {
                Priority.HIGH.value: "#ff4c4c",
                Priority.MEDIUM.value: "#f2eb1d",
                Priority.LOW.value: "#59d95e",
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
                annotations=[dict(
                    text=pmo_table.NAME_COLUMN_PRIORITY, x=0.5, y=0.5, font_size=20, showarrow=False)]
            )

            # Display the chart in Streamlit
            st.plotly_chart(fig)
