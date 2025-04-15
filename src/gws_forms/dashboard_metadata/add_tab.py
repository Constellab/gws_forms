import streamlit as st
from gws_forms.dashboard_metadata.metadata_state import MetadataState
from gws_core.streamlit import StreamlitContainers

def render_add_tab(metadata_state : MetadataState):

    style = """
    [CLASS_NAME] {
        border: 3px solid grey;
        padding: 1em;
    }
    """

    with StreamlitContainers.container_centered('container-center', max_width='48em',
                additional_style=style):
        # Get the existing Json Metadata file into a dict
        metadata_json = metadata_state.get_metadata_json()

        st.write("**Define Metadata**")

        st.text_input(label = "Name", placeholder = "Enter the name of your metadata", key = "name_metadata")

        st.text_input(label = "Description", placeholder = "Describe your metadata", key = "description")

        st.selectbox("Response type", ["options", "numeric"], key = "metadata_type")
        if metadata_state.get_metadata_type() == "options":
            # Get current number of allowed values
            number_allowed_values = metadata_state.get_allowed_values_number()
            st.write("Allowed values")
            # Create inputs
            for i in range(1, number_allowed_values + 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text_input(label="Allowed values", placeholder="Enter the name of your metadata", label_visibility = "collapsed", key=f"allowed_values_{i}")
                with col2:
                    if i == number_allowed_values:
                        # Last row: text input + '+' button in a horizontal layout
                        if st.button("\+", type = "primary", key="add_value_button"):
                            number_allowed_values += 1
                            metadata_state.set_allowed_values_number(number_allowed_values)
                            st.rerun()

        if metadata_state.get_metadata_type() == "numeric":
            st.number_input("Minimum Value", key = "min_value")
            st.number_input("Maximum Value", key = "max_value")

        # If not all fields are completed, raises a warning
        if not metadata_state.get_name_metadata():
            submit_disabled = True
            st.write(":red[Please complete all the fields]")
        else :
            submit_disabled = False

        # Check if name already exists
        existing_entry = metadata_state.get_existing_entry(value_user = False)

        if existing_entry and existing_entry["response_type"] != metadata_state.get_metadata_type():
            # Check response_type consistency
            st.warning(f"⚠️ The response type for '{metadata_state.get_name_metadata()}' does not match the existing entry. It should be '{existing_entry['response_type']}' ")
            return

        # Submit button to add the metadata
        if st.button("Submit", disabled = submit_disabled, icon = ":material/save:", on_click = metadata_state.clear_fields):

            # New metadata entry
            new_entry = metadata_state.get_new_entry()

            # Check if name already exists
            existing_entry = metadata_state.get_existing_entry(value_user = True)
            if existing_entry:
                # Replace description
                existing_entry["description"] = new_entry["description"]

                # Merge allowed values, avoiding duplicates
                existing_values = set(existing_entry.get("allowed_values", []))
                new_values = set(new_entry.get("allowed_values", []))
                existing_entry["allowed_values"] = sorted(existing_values.union(new_values))

                # Update min and max values if provided
                if new_entry["min_value"] is not None:
                    existing_entry["min_value"] = new_entry["min_value"]
                if new_entry["max_value"] is not None:
                    existing_entry["max_value"] = new_entry["max_value"]

                # Update the value in the existing dict
                for idx, entry in enumerate(metadata_json["metadata"]):
                    if entry.get("name") == metadata_state.get_name_metadata_user():
                        metadata_json["metadata"][idx] = existing_entry
                        break

                st.success(f"✅ Metadata for '{new_entry['name']}' updated.")
            else:
                metadata_json["metadata"].append(new_entry)
                st.success(f"✅ Metadata for '{new_entry['name']}' added.")

            # Save back to file
            metadata_state.save_metadata_json(metadata_json)
