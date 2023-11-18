import os
import json

import logging
logger = logging.getLogger('discord')

# load from defaults/settings.json if it doesn't exist
DEFAULTS = {"posting_timer": 300,
            "channel_id": 1234567890,
            "server_whitelist":[],
            "active": True,
            "repetition_odds":3,
            "max_length": 200,
            "num_prompts": 1,
            "cooldown_max": 7200,
            "cooldown_min": 1200,
            "cooldown_adustment": 1800,
            "lookback": 3,
            "message_list": [],
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

def save_settings(setting):
    logger.info("Saving settings...")
    #sanity check values in settings
    setting["posting_timer"] = max(int(setting["posting_timer"]), 10)
    setting["repetition_odds"] = max(int(setting["repetition_odds"]), 0)
    setting["max_length"] = min(int(setting["max_length"]), 400)
    setting["num_prompts"] = min(int(setting["num_prompts"]), 20)
    setting["cooldown_max"] = max(int(setting["cooldown_max"]), 600)
    setting["cooldown_min"] = max(int(setting["cooldown_min"]), 0)
    setting["lookback"] = max(int(setting["lookback"]), 1)
    # Write settings.json
    with open('settings.json', 'w') as f:
        json.dump(setting, f)