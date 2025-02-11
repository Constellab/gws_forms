import os
import json
from datetime import datetime
import pytz

# Function to load previous sessions (returns list of session filenames)
def list_sessions(session_directory : str):
    return [f.split(".json")[0] for f in os.listdir(session_directory) if f.endswith(".json")]


# Function to load a specific session
def load_session(session_name : str, session_directory : str):
    session_path = os.path.join(session_directory, session_name)
    if os.path.exists(session_path):
        with open(session_path, "r") as f:
            return json.load(f)
    return {}

# Function to save the current session
def save_current_session(questions, session_directory : str, name_user : str):
    timestamp = datetime.now(tz=pytz.timezone('Europe/Paris')).strftime(f"session-{name_user}-%d_%m_%Y-%Hh%M.json")
    path = os.path.join(session_directory, timestamp)
    session_data = {"questions": questions}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False)
