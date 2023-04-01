import os
from typing import Dict

import yaml


def replace_variables(config: Dict, env_vars: Dict) -> Dict:
    for key, value in config.items():
        if isinstance(value, str):
            config[key] = value.format(**env_vars)
        elif isinstance(value, dict):
            config[key] = replace_variables(value, env_vars)
    return config


def read_config(config_file_path: str) -> Dict:
    env_vars = {
        "POSTGRES_USER": os.environ.get("POSTGRES_USER", ""),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST", ""),
        "POSTGRES_PORT": os.environ.get("POSTGRES_PORT", ""),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB", ""),
        "KAFKA_HOST": os.environ.get("KAFKA_HOST", ""),
        "KAFKA_PORT": os.environ.get("KAFKA_PORT", ""),
        "KAFKA_TOPIC": os.environ.get("KAFKA_TOPIC", "")
    }

    with open(config_file_path, "r") as config_file:
        config = yaml.safe_load(config_file)

    config = replace_variables(config, env_vars)

    return config
