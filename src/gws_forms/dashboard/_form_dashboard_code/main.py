import json
import os
import random
import re

import streamlit as st
from gws_core.space.space_dto import SpaceSendMailToMailsDTO
from gws_core.space.space_service import SpaceService
from session_management.session_functions import (load_session,
                                                  save_current_session)

# thoses variable will be set by the streamlit app
# don't initialize them, there are create to avoid errors in the IDE
sources: list
params: dict

json_questions = sources[0]
folder_path_session = sources[1].path

st.markdown(
    "<style>[data-testid='stMain'] {display: flex; flex-direction: column;} [data-testid='stMainBlockContainer'] {max-width: 60rem; margin: 0 auto;} [data-testid='stExpander'] {background-color: #eaeaea;} </style>",
    unsafe_allow_html=True)


def border_left_red(component: str):
    # replace special characters and space by a dash
    regex = r"[^a-zA-Z0-9]"
    component = re.sub(regex, "-", component)

    css = f".st-key-{component} " + \
        "{border-left: 8px solid #49a8a9;border-radius: 8px;padding-left: 16px;background-color: #ffffff; padding-bottom: 12px;} " + \
        f".st-key-{component} > div " + "{max-width: calc(100% - 24px);}" + \
        f".st-key-{component} > div  div " + "{max-width: 100%;}"
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)


st.image(image=params['banner'])

st.title(params['title'])
st.markdown(params['description'])

# Fonction pour regrouper les questions par section et sous-section


def get_questions_by_section(questions):
    sections = {}
    for question in questions:
        section = question['section']
        if section not in sections:
            sections[section] = []
        sections[section].append(question)
    return sections


# Function to check if all required questions are answered
def all_required_answered(answer_questions, conf_questions):
    for question_data in conf_questions:
        for answer_question in answer_questions:
            if question_data["section"] == answer_question["section"] and question_data["question"] == answer_question["question"]:
                question_data["answer"] = answer_question["answer"]
                break

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


def is_valid_email(email: str):
    if not email:
        return False
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def generate_session_token(email: str) -> int:
    # Generate a random session token
    random.seed(email)
    return random.randint(100000, 999999)


def send_mail(email: str, token: int):
    mail_data = SpaceSendMailToMailsDTO(
        receiver_mails=[email],
        mail_template="generic",
        data={
            'content': f"Your form session token is : {token}."
        },
        subject=f"Form {params['title']} - Session token"
    )
    SpaceService.get_instance().send_mail_to_mails(mail_data)


def store_session_token(email: str, token: int):
    # Store the session token in a file
    with open(os.path.join(folder_path_session, "sessions-token.json"), "w", encoding="utf8") as f:
        json.dump({email: token}, f)


def get_session_token(email: str) -> str:
    # Load the session token from the file
    with open(os.path.join(folder_path_session, "sessions-token.json"), "r", encoding="utf8") as f:
        return json.load(f).get(email, None)


def delete_session_token(email: str) -> None:
    # Delete the session token from the file
    with open(os.path.join(folder_path_session, "sessions-token.json"), "r", encoding="utf8") as f:
        data = json.load(f)
        if email in data:
            del data[email]
    with open(os.path.join(folder_path_session, "sessions-token.json"), "w", encoding="utf8") as f:
        json.dump(data, f)


def check_session_token(email: str, token: int) -> bool:
    # Check if the session token is valid
    return token == get_session_token(email)


def session_token_exists(email: str) -> bool:
    # Check if the session token exists
    with open(os.path.join(folder_path_session, "sessions-token.json"), "r", encoding="utf8") as f:
        return email in json.load(f)


@st.fragment
def question_component(section, question_number, question_data):
    with st.container(key=f"{section}-{question_number}"):
        border_left_red(f"{section}-{question_number}")
        question_key = question_data['question']
        st.markdown(
            f"##### {question_number}. {question_data.get('question_head')}: {question_key}")
        st.write(question_data['helper_text'])

        # Populate answers from saved session if available
        questions_json = st.session_state['saved_answers'].get('questions', [])
        saved_answer = next(
            (question["answer"] for question in questions_json
                if question["section"] == section and question["question"] == question_key),
            None)

        # Générer le champ correspondant au type de réponse attendu
        response = None
        if question_data.get('allowed_values'):
            if question_data.get('multiselect'):
                response = st.multiselect(
                    label=question_key, label_visibility="collapsed",
                    options=question_data['allowed_values'],
                    default=saved_answer if saved_answer else [],
                    placeholder="Select a single or several options")

            else:
                response = st.selectbox(
                    label=question_key, label_visibility="collapsed",
                    options=question_data['allowed_values'],
                    index=question_data['allowed_values'].index(saved_answer)
                    if saved_answer in question_data['allowed_values'] else None,
                    placeholder="Select an option")
        else:
            if question_data['response_type'] == "short_text":
                response = st.text_input(
                    label=question_key, label_visibility="collapsed",
                    placeholder="Enter a response", value=saved_answer if saved_answer else None)
            elif question_data['response_type'] == "long_text":
                response = st.text_area(
                    label=question_key, label_visibility="collapsed", value=saved_answer
                    if saved_answer else None, placeholder="Enter a response",
                    key=f"{section}-{question_number}-input")
            elif question_data['response_type'] == "numeric":
                response = st.number_input(
                    label=question_key, label_visibility="collapsed", value=saved_answer
                    if saved_answer else None, min_value=question_data.get('min_value', None),
                    max_value=question_data.get('max_value', None),
                    placeholder="Enter a number")
            elif question_data['response_type'] == "range":
                response = st.slider(
                    label=question_key, label_visibility="collapsed", value=saved_answer
                    if saved_answer else None, min_value=question_data.get('min_value', None),
                    max_value=question_data.get('max_value', None),
                    placeholder="Select a range")
        # Update the original JSON structure with the captured answer
        question_data['answer'] = response
        # check if question is in questions_json
        question_exists = next(
            (question for question in questions_json
                if question["section"] == section and question["question"] == question_key),
            None)

        # Si la question est obligatoire
        if question_data.get(
                "required", True) and (
                response is None or response == "" or response == []):
            st.write(":red[*Required]")
            if question_exists:
                # Update the saved answers with the current question
                for question in questions_json:
                    if question["section"] == section and question["question"] == question_key:
                        question["answer"] = response
        else:
            if not question_exists:
                # Add the current question to the saved answers
                questions_json.append(question_data)
            else:
                # Update the saved answers with the current question
                for question in questions_json:
                    if question["section"] == section and question["question"] == question_key:
                        question["answer"] = response

        save_current_session(
            questions=questions_json, session_directory=SESSIONS_DIR,
            token=st.session_state['token'])


@st.fragment
def submit():
    save_current_session(
        questions=st.session_state['saved_answers']['questions'],
        session_directory=SESSIONS_SUBMITTED_DIR, token=st.session_state['token'],
        multi=True)
    st.session_state['submitted'] = True


def show_content():
    tab_questions = None
    tab_visu = None

    if params['results_visible']:
        tab_questions, tab_visu = st.tabs(["Questions", "Charts"])
    # Create tabs
    else:
        tab_questions = st.tabs(["Questions"])[0]

    with tab_questions:
        if 'first_email_run' not in st.session_state:
            st.session_state['first_email_run'] = False

        col1, col2 = st.columns([5, 1], vertical_alignment="bottom")
        if 'email_validated' not in st.session_state:
            st.session_state['email_validated'] = False
        confirm_email_button = None
        change_email_button = None

        with col1:
            st.session_state['email'] = st.text_input(
                label="Enter your email", placeholder="Email", disabled=st.session_state['email_validated'])
        with col2:
            if not st.session_state['email_validated']:
                confirm_email_button = st.button("Confirm email", key="confirm_email")
            else:
                change_email_button = st.button("Change email", key="change_email")

        if confirm_email_button is not None and confirm_email_button:
            if not is_valid_email(st.session_state['email']):
                st.error("Please enter a valid email address.")
            else:
                st.session_state['email_validated'] = True
                st.rerun()

        if change_email_button is not None and change_email_button:
            st.session_state['email_validated'] = False
            st.session_state['token_validated'] = False
            st.rerun()

        if not st.session_state['email_validated']:
            st.stop()

        if not session_token_exists(st.session_state['email']):
            session_token = generate_session_token(st.session_state['email'])
            store_session_token(st.session_state['email'], session_token)
            send_mail(st.session_state['email'], session_token)
            st.session_state['first_email_run'] = True

            st.write("A session token has been sent to your email. Please check your inbox and use it next time you come to this form.")

        if not st.session_state['first_email_run']:
            confirm_token_button = None
            change_token_button = None
            col1, col2 = st.columns([5, 1], vertical_alignment="bottom")

            if 'token_validated' not in st.session_state:
                st.session_state['token_validated'] = False

            with col1:
                st.session_state['token'] = st.text_input(
                    label="Enter your session token", placeholder="Token", disabled=st.session_state['token_validated'])
            with col2:
                if not st.session_state['token_validated']:
                    confirm_token_button = st.button("Confirm token", key="confirm_token")
                else:
                    change_token_button = st.button("Change token", key="change_token")

            if confirm_token_button is not None and confirm_token_button:
                # check if token is numeric and valid
                if st.session_state['token'].isnumeric() and check_session_token(
                        st.session_state['email'],
                        int(st.session_state['token'])):
                    st.session_state['token_validated'] = True
                    st.rerun()
                else:
                    st.error("Invalid session token. Please check your email and try again.")

            if change_token_button is not None and change_token_button:
                st.session_state['token_validated'] = False
                st.rerun()

            if not st.session_state['token_validated']:
                st.stop()
        else:
            st.session_state['token'] = get_session_token(st.session_state['email'])

        st.markdown("---")

        if 'saved_answers' not in st.session_state:
            st.session_state['saved_answers'] = load_session(
                session_directory=SESSIONS_DIR, token=st.session_state['token'])

        # Regrouper les questions par section
        sections = get_questions_by_section(
            json_questions['questions'])

        question_number = 1
        # Parcourir chaque section et afficher les questions correspondantes
        for section, questions in sections.items():
            st.header(section)
            with st.expander(section, expanded=True, icon=":material/edit_note:"):
                # Loop through each question in the section
                for question_data in questions:
                    question_component(section, question_number, question_data)
                    question_number += 1
                st.markdown("---")

        st.session_state['saved_answers'] = load_session(session_directory=SESSIONS_DIR,
                                                         token=st.session_state['token'])
        # Submit button will only be enabled if all required answers are filled
        submit_disabled = not all_required_answered(
            answer_questions=st.session_state['saved_answers']['questions'], conf_questions=json_questions['questions'])

        # Bouton de soumission (disabled if not all required fields are filled)
        st.write(
            "Submit the form once completed. Please note that after submission, the form can no longer be edited.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.button("Submit", disabled=submit_disabled, type="primary",
                      use_container_width=True, key="submit", on_click=submit)
            if 'submitted' in st.session_state:
                st.success("Form submitted successfully.")
                del st.session_state['submitted']

    if params['results_visible']:
        with tab_visu:
            st.write("## Viewing submitted sessions")
            show_submitted_sessions(submitted_directory=SESSIONS_SUBMITTED_DIR)


# Create a directory for saving sessions if it doesn't exist
SESSIONS_DIR = os.path.join(folder_path_session, "saved_sessions")
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# Create a directory for saving submitted sessions if it doesn't exist
SESSIONS_SUBMITTED_DIR = os.path.join(
    folder_path_session, "submitted_sessions")
if not os.path.exists(SESSIONS_SUBMITTED_DIR):
    os.makedirs(SESSIONS_SUBMITTED_DIR)

# init sessions-token.json if it doesn't exist
if not os.path.exists(os.path.join(folder_path_session, "sessions-token.json")):
    with open(os.path.join(folder_path_session, "sessions-token.json"), "w", encoding="utf8") as f:
        json.dump({}, f)

show_content()
