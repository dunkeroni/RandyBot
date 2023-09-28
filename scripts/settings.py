import os
import json

DEFAULTS = {
    "posting_timer": 3600,
    "spam_prevention": False,
}

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

def set_settings(settings):
    # Initialize settings.json if it doesn't exist
    initialize()

    # Write settings.json
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

    