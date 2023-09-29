import os
import json

# load from defaults/settings.json if it doesn't exist
DEFAULTS = {"posting_timer": 300, "channel_id": 1234567890, "server_whitelist":[], "active": True}

def initialize():
    # Initialize settings.json if it doesn't exist
    if not os.path.exists('settings.json'):
        with open('settings.json', 'w') as f:
            json.dump(DEFAULTS, f)

def get_settings():
    # Initialize settings.json if it doesn't exist
    initialize()

    # Read settings.json
    with open('settings.json', 'r') as f:
        settings = json.load(f)

    return settings

def save_settings(settings):
    # Write settings.json
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

    