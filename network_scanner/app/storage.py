import json
import os

import threading

seen_file_lock = threading.Lock()
user_config_file_lock = threading.Lock()

def update_json_file(path, lock, updater):
    with lock:
        data = load_json(path)

        if not isinstance(data, dict):
            data = {}

        updated_data = updater(data)
        save_json(path, updated_data)

        return updated_data

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

        