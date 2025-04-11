import os
import json
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__))).parent
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
WORD_LISTS_DIR = os.path.join(PROJECT_ROOT, "utils", "word_lists")

# Ensure directories exist
for directory in [DATA_DIR, LOGS_DIR, WORD_LISTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# API settings
API_SETTINGS = {
    "gemini": {
        "model": "gemini-2.5-pro-exp-03-25",
        "api_key_env": "GEMINI_API_KEY"
    },
    "timeout_seconds": 12,
    "max_retries": 3
}

def load_config_file(filename):
    """Load a configuration file from the project root"""
    config_path = os.path.join(PROJECT_ROOT, filename)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config file {filename}: {e}")
    return {}

# Load user configuration if available (overrides defaults)
user_config = load_config_file("config.json")
if user_config:
    # Update API settings with user-defined values
    if "api_settings" in user_config:
        for key, value in user_config["api_settings"].items():
            if key in API_SETTINGS:
                if isinstance(value, dict) and isinstance(API_SETTINGS[key], dict):
                    # Update nested dictionaries
                    API_SETTINGS[key].update(value)
                else:
                    # Replace simple values
                    API_SETTINGS[key] = value
