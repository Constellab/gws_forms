import json
import os
from datetime import datetime

import pytz


def load_session(session_directory: str, token: str) -> dict:
    path = os.path.join(session_directory, f"session_{token}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

# Function to save the current session


def save_current_session(questions: list, session_directory: str, token: str, multi: bool = False):
    timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime("%d-%m-%Y-%H-%M-%S")
    path = os.path.join(session_directory, f"session_{token}.json")
    if multi:
        path = os.path.join(session_directory, f"session_{token}_{timestamp}.json")
    session_data = {"questions": questions, "timestamp": timestamp}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False)
