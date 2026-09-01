"""
Configuration loader for fraud detection settings.
"""

import json
from pathlib import Path


DEFAULT_CONFIG = {
    "high_value_threshold": 5000,
    "declined_count_threshold": 4,
    "location_count_threshold": 3,
    "time_window_minutes": 30,
    "declined_in_window_threshold": 4,
    "rules": {},
}


def load_config(filepath="config.json"):
    """
    Load fraud detection configuration from a JSON file.

    Args:
        filepath: Path to the JSON configuration file.

    Returns:
        A dictionary of configuration settings. Falls back to defaults
        if the file is missing or invalid.
    """
    path = Path(filepath)

    if not path.exists():
        print(f"Warning: Config file '{filepath}' not found. Using defaults.")
        return DEFAULT_CONFIG.copy()

    try:
        with path.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Warning: Unable to load config '{filepath}' - {exc}. Using defaults.")
        return DEFAULT_CONFIG.copy()

    merged = DEFAULT_CONFIG.copy()
    merged.update(config)
    return merged
