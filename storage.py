import os
import json

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def save_user_data(user_id, data):
    user_file = os.path.join(DATA_DIR, f"{user_id}.json")
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_user_data(user_id):
    user_file = os.path.join(DATA_DIR, f"{user_id}.json")
    if os.path.exists(user_file):
        with open(user_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def update_user_data(user_id, new_data):
    data = load_user_data(user_id)
    data.update(new_data)
    save_user_data(user_id, data)
