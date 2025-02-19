import json
import os
from datetime import datetime

import pytz
import streamlit as st


def load_session(session_directory: str, token: str) -> dict:
    path = os.path.join(session_directory, f"session_{token}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {'questions': []}

# Function to save the current session


def save_current_session(questions: list, session_directory: str, token: str, multi: bool = False):
    timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime("%d-%m-%Y-%H-%M-%S")
    path = os.path.join(session_directory, f"session_{token}.json")
    session_data = {"questions": questions, "timestamp": timestamp}
    # check if the file content is different from the current session, if it's different save the session + st.rerun
    if multi:
        path = os.path.join(session_directory, f"session_{token}_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False)
        return
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            if data != session_data:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(session_data, f, ensure_ascii=False)
                st.rerun()
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False)
            st.rerun()
