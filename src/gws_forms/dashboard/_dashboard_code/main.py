import os
import json
import streamlit as st
from session_management.session_functions import list_sessions, load_session, save_current_session

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict


# Your Streamlit app code here
st.title("Questionnaire dashboard")

# Fonction pour regrouper les questions par section et sous-section


def get_questions_by_section_and_subsection(questions):
    sections = {}
    for question in questions:
        section = question['section']
        subsection = question.get('subsection', None)
        if section not in sections:
            sections[section] = {}
        if subsection:
            if subsection not in sections[section]:
                sections[section][subsection] = []
            sections[section][subsection].append(question)
        else:
            if None not in sections[section]:
                sections[section][None] = []
            sections[section][None].append(question)
    return sections


# Function to check if all required questions are answered
def all_required_answered(questions):
    for question_data in questions:
        if question_data["required"] and (question_data["answer"] is None or question_data["answer"] == ""):
            return False
    return True


def show_submitted_sessions(submitted_directory: str):
    # List all JSON files in the submitted directory
    files = [f.split(".json")[0] for f in os.listdir(
        submitted_directory) if f.endswith(".json")]
    # If there are files, show a selectbox to choose one
    if files:
        selected_file = st.selectbox(label="Choose an existing session",
                                     options=files, index=None, placeholder="Select a session")

        # Load the selected file and display its contents
        if selected_file:
            selected_file = selected_file + ".json"
            file_path = os.path.join(submitted_directory, selected_file)
            with open(file_path, "r", encoding="utf-8") as f:
                submitted_data = json.load(f)

            # Download answers as JSON file
            st.download_button(label="Download submitted responses",
                               data=json.dumps(
                                   submitted_data, indent=4, ensure_ascii=False).encode('utf-8'),
                               file_name='answers.json', mime='application/json')
            # Show the content of the selected file in a JSON format
            st.write("### Content of the submitted session:")
            st.json(submitted_data)
    else:
        st.write("No submitted session found.")


def show_content():

    # Create tabs
    tab_questions, tab_visu = st.tabs(["Questions", "Charts"])

    with tab_questions:
        # User choice: new session or continue previous one
        session_list = list_sessions(session_directory=SESSIONS_DIR)
        session_choice = None
        if session_list:
            session_choice = st.selectbox(label="Select a previous session to load it.", options=session_list, index=None,
                                          placeholder="Select a session")
            if session_choice:
                session_choice = session_choice + ".json"

        st.markdown("---")

        # User name
        name_user = st.text_input(label="Enter a name", placeholder="Enter a response",
                                  value=session_choice.split("-")[1] if session_choice else "")

        # Load previous answers if available
        saved_answers = load_session(
            session_name=session_choice, session_directory=SESSIONS_DIR) if session_choice else {}

        # Regrouper les questions par section
        sections = get_questions_by_section_and_subsection(
            json_questions['questions'])

        # Parcourir chaque section et afficher les questions correspondantes
        for section, subsections in sections.items():
            st.header(section)

            for subsection, questions in subsections.items():
                if subsection:
                    st.subheader(subsection)

                # Loop through each question in the section
                for question_data in questions:
                    question_key = question_data['question']
                    st.markdown(f"#### {question_key}")
                    st.write(question_data['helper_text'])

                    # Populate answers from saved session if available
                    questions_json = saved_answers.get('questions', {})
                    saved_answer = next((question["answer"] for question in questions_json
                                            if question["section"] == section and question["question"] == question_key), None)

                    # Générer le champ correspondant au type de réponse attendu
                    response = None
                    if question_data.get('allowed_values'):
                        if question_data.get('multiselect'):
                            response = st.multiselect(label=question_key, label_visibility="collapsed",
                                                          options=question_data['allowed_values'], default=saved_answer if saved_answer else [], placeholder="Select a single or several options")

                        else:
                            response = st.selectbox(label=question_key, label_visibility="collapsed", options=question_data['allowed_values'],
                                                        index=question_data['allowed_values'].index(saved_answer) if saved_answer in question_data['allowed_values'] else None, placeholder="Select an option")
                    else:
                        if question_data['response_type'] == "short_text":
                            response = st.text_input(label=question_key, label_visibility="collapsed",
                                                         placeholder="Enter a response", value=saved_answer if saved_answer else None)
                        elif question_data['response_type'] == "long_text":
                            response = st.text_area(label=question_key, label_visibility="collapsed",
                                                        placeholder="Enter a response", value=saved_answer if saved_answer else None)
                        elif question_data['response_type'] == "numeric":
                            response = st.number_input(label=question_key, label_visibility="collapsed",
                                                           value=saved_answer if saved_answer else None, min_value=question_data.get('min_value', None),
                                                           max_value=question_data.get('max_value', None), placeholder="Enter a number")
                        elif question_data['response_type'] == "range":
                            response = st.slider(label=question_key, label_visibility="collapsed",
                                                     value=saved_answer if saved_answer else None, min_value=question_data.get('min_value', None),
                                                     max_value=question_data.get('max_value', None), placeholder="Select a range")
                    # Update the original JSON structure with the captured answer
                    question_data['answer'] = response

                    # Si la question est obligatoire
                    if question_data.get("required", True) and (response is None or response == "" or response == []):
                        st.write(":red[*Required]")

                st.markdown("---")

        # Submit button will only be enabled if all required answers are filled
        submit_disabled = not all_required_answered(
            json_questions['questions'])

        # Save button
        st.write(
            "Save the session to complete your responses later.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Save session", use_container_width=True):
                save_current_session(
                    questions=json_questions['questions'], session_directory=SESSIONS_DIR, name_user=name_user)
                # Delete the file where the session was saved if it's not a new session
                if session_choice:
                    session_path = os.path.join(SESSIONS_DIR, session_choice)
                    # Check if the file exists and delete it
                    if os.path.exists(session_path):
                        os.remove(session_path)
                st.success("Session saved !")

        # Bouton de soumission (disabled if not all required fields are filled)
        st.write(
            "Submit the form once completed. Please note that after submission, the form can no longer be edited.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Submit", disabled=submit_disabled, type="primary", use_container_width=True):
                save_current_session(
                    questions=json_questions['questions'], session_directory=SESSIONS_SUBMITTED_DIR, name_user=name_user)
                # Delete the file where the session was saved if it's not a new session
                if session_choice:
                    session_path = os.path.join(SESSIONS_DIR, session_choice)
                    # Check if the file exists and delete it
                    if os.path.exists(session_path):
                        os.remove(session_path)
                st.success("Form successfully submitted!")

    with tab_visu:
        st.write("## Viewing submitted sessions")
        show_submitted_sessions(submitted_directory=SESSIONS_SUBMITTED_DIR)


json_questions = sources[0]
folder_path_session = sources[1].path

# Create a directory for saving sessions if it doesn't exist
SESSIONS_DIR = os.path.join(folder_path_session, "saved_sessions")
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# Create a directory for saving submitted sessions if it doesn't exist
SESSIONS_SUBMITTED_DIR = os.path.join(
    folder_path_session, "submitted_sessions")
if not os.path.exists(SESSIONS_SUBMITTED_DIR):
    os.makedirs(SESSIONS_SUBMITTED_DIR)

show_content()
