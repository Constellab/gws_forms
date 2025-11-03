import json
import os

import streamlit as st
from gws_core import FrontService, JSONDict, ResourceModel, ResourceOrigin

from gws_forms.dashboard_creation._dashboard_code.session_management.session_functions import (
    list_sessions, load_session, save_current_session)

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

# Streamlit app title
# st.title("Questionnaire Creation Dashboard")

folder_path_session = sources[0].path

# Create a directory for saving sessions if it doesn't exist
SESSIONS_DIR = os.path.join(folder_path_session, "saved_sessions")
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# Create a directory for saving submitted sessions if it doesn't exist
SESSIONS_SUBMITTED_DIR = os.path.join(folder_path_session, "submitted_sessions")
if not os.path.exists(SESSIONS_SUBMITTED_DIR):
    os.makedirs(SESSIONS_SUBMITTED_DIR)

# Initialize session state to store questions
if 'questions' not in st.session_state:
    st.session_state.questions = []

if "blank_text" not in st.session_state:
    st.session_state.blank_text = ""


def clear_fields():
    # Retrieve values
    st.session_state["section"] = st.session_state["Section"]
    st.session_state["subsection"] = st.session_state["Subsection"]
    st.session_state["question_head"] = st.session_state["Question_head"]
    st.session_state["question"] = st.session_state["Question"]
    st.session_state["helper_text"] = st.session_state["Helper_text"]
    st.session_state["is_required"] = st.session_state["Is_required"]
    st.session_state["response_type"] = st.session_state["Response_type"]

    if "Min_value" in st.session_state:
        st.session_state["min_value"] = st.session_state["Min_value"]
        st.session_state["Min_value"] = None
    if "Max_value" in st.session_state:
        st.session_state["max_value"] = st.session_state["Max_value"]
        st.session_state["Max_value"] = None
    if "Multi_select" in st.session_state:
        st.session_state["multi_select"] = st.session_state["Multi_select"]
        st.session_state["Multi_select"] = False
    if "Allowed_values" in st.session_state:
        st.session_state["allowed_values"] = st.session_state["Allowed_values"]
        st.session_state["Allowed_values"] = ""

    # Clear the fields
    st.session_state["Section"] = ""
    st.session_state["Subsection"] = ""
    st.session_state["Question_head"] = ""
    st.session_state["Question"] = ""
    st.session_state["Helper_text"] = ""
    st.session_state["Is_required"] = False
    st.session_state["Response_type"] = "long_text"

# Function to show content in tabs


def show_content():

    # Create tabs
    tab_creation, tab_questions = st.tabs(["Create a new question", "Submitted questions"])

    with tab_creation:
        # User choice: new session or continue previous one
        session_list = list_sessions(session_directory=SESSIONS_DIR)
        session_choice = st.selectbox("Select a previous session to load it.",
                                      options=session_list, index=None) if session_list else None
        if session_choice:
            session_choice = session_choice + ".json"
            # Load previous answers if available
            saved_answers = load_session(session_name=session_choice,
                                         session_directory=SESSIONS_DIR) if session_choice else {}
            # Initialize session state to store the first time to load data
            if 'load_data' not in st.session_state:
                st.session_state.load_data = []
                st.session_state.questions = saved_answers.get('questions', [])

        # User name
        name_user = st.text_input(label="Enter a name", placeholder="Enter a response",
                                  value=session_choice.split("-")[1] if session_choice else "")
        st.markdown("---")

        st.write("**Create a new question**")
        # Initiate values
        multi_select = False
        min_value = None
        max_value = None
        allowed_values = None

        # Input fields for question details
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            section = st.text_input(label="Section", placeholder="Enter a section name", key="Section")
        with col2:
            subsection = st.text_input(label="Subsection", placeholder="Enter a subsection name", key="Subsection")
        with col3:
            question_head = st.text_input(
                label="Question_head", placeholder="Enter a keyword for your question", key="Question_head")
        question = st.text_input(label="Question", placeholder="Enter the question", key="Question")
        helper_text = st.text_input(
            "Helper Text", placeholder="Provide some context for the question", key="Helper_text")
        is_required = st.checkbox("Is this question required?", key="Is_required")

        response_type = st.selectbox(
            "Response Type", ["long_text", "short_text", "option", "numeric"],
            key="Response_type")
        if response_type == "option":
            allowed_values = st.text_area("Allowed Values (comma-separated)",
                                          placeholder="e.g., Yes, No, Maybe", key="Allowed_values")
            multi_select = st.checkbox("Allow Multiple Selections", key="Multi_select")
        if response_type == "numeric":
            min_value = st.number_input("Minimum Value", key="Min_value")
            max_value = st.number_input("Maximum Value", key="Max_value")

        if section == "" or question == "" or allowed_values == "":
            submit_disabled = True
            st.write(":red[Please complete all the fields]")
        else:
            submit_disabled = False

        # Submit button to add the question
        if st.button("Submit Question", disabled=submit_disabled, on_click=clear_fields):
            question = {
                "section": st.session_state["section"],
                "subsection": st.session_state["subsection"],
                "question_head": st.session_state["question_head"],
                "question": st.session_state["question"],
                "response_type": st.session_state["response_type"],
                "allowed_values": st.session_state["allowed_values"].split(",")
                if "allowed_values" in st.session_state else [], "multiselect": st.session_state["multi_select"]
                if "multi_select" in st.session_state else False, "min_value": st.session_state["min_value"]
                if "min_value" in st.session_state else None, "max_value": st.session_state["max_value"]
                if "max_value" in st.session_state else None, "required": st.session_state["is_required"],
                "helper_text": st.session_state["helper_text"]}
            # Store question in the dictionary with an index as the key
            index = len(st.session_state.questions)  # next index
            st.session_state.questions.append(question)
            st.success(f"Question {index + 1} added!")

        if st.session_state.questions:
            st.markdown("---")

            # Save button
            st.write(
                "Save the session to complete your questions later.")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("Save session", use_container_width=True, key="save_end"):
                    save_current_session(questions=st.session_state.questions,
                                         session_directory=SESSIONS_DIR, name_user=name_user)
                    # Delete the file where the session was saved if it's not a new session
                    if session_choice:
                        session_path = os.path.join(SESSIONS_DIR, session_choice)
                        # Check if the file exists and delete it
                        if os.path.exists(session_path):
                            os.remove(session_path)
                    st.success("Session saved !")

            # Submit button
            st.write("Submit the form when finished. Please note that after submission, the form can no longer be edited.")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("Submit", type="primary", use_container_width=True):
                    save_current_session(questions=st.session_state.questions,
                                         session_directory=SESSIONS_SUBMITTED_DIR, name_user=name_user)
                    # Delete the file where the session was saved if it's not a new session
                    if session_choice:
                        session_path = os.path.join(SESSIONS_DIR, session_choice)
                        # Check if the file exists and delete it
                        if os.path.exists(session_path):
                            os.remove(session_path)
                    # Create a Json Dict
                    json_dict: JSONDict = JSONDict()
                    json_dict.data = {"questions": st.session_state.questions}
                    json_resource = ResourceModel.save_from_resource(json_dict, ResourceOrigin.UPLOADED, flagged=True)

                    st.success(
                        f"Form successfully submitted! A JsonDict Resource has been created : {FrontService.get_resource_url(json_resource.id)}")

    with tab_questions:

        # Display the submitted questions
        if st.session_state.questions:
            # Download JSON button
            formatted_questions = {"questions": st.session_state.questions}
            # Convert questions to JSON
            json_data = json.dumps(formatted_questions, indent=4)
            st.download_button(
                label="Download Questions JSON",
                data=json_data,
                file_name="questions.json",
                mime="application/json"
            )

            idx = 0
            for question in st.session_state.questions:
                st.write(f"**Question {idx + 1 }:**")
                st.json(question)
                idx += 1

        else:
            st.write("No questions submitted yet.")

# ""


show_content()
