import json
import os
import threading

import config

_lock = threading.Lock()


def _load():
    if not os.path.exists(config.DATA_FILE):
        return {}
    try:
        with open(config.DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def _save(data):
    with open(config.DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_group_settings(chat_id) -> dict:
    data = _load()
    return data.get(str(chat_id), {})


def set_group_setting(chat_id, key, value):
    with _lock:
        data = _load()
        chat_key = str(chat_id)
        data.setdefault(chat_key, {})
        data[chat_key][key] = value
        _save(data)


def get_warns(chat_id, user_id) -> int:
    data = _load()
    chat_key = str(chat_id)
    warns = data.get(chat_key, {}).get("warns", {})
    return warns.get(str(user_id), 0)


def add_warn(chat_id, user_id) -> int:
    """Increments and returns the new warn count for user_id in chat_id."""
    with _lock:
        data = _load()
        chat_key = str(chat_id)
        data.setdefault(chat_key, {})
        data[chat_key].setdefault("warns", {})
        user_key = str(user_id)
        current = data[chat_key]["warns"].get(user_key, 0) + 1
        data[chat_key]["warns"][user_key] = current
        _save(data)
        return current


def reset_warns(chat_id, user_id):
    with _lock:
        data = _load()
        chat_key = str(chat_id)
        if chat_key in data and "warns" in data[chat_key]:
            data[chat_key]["warns"].pop(str(user_id), None)
            _save(data)
