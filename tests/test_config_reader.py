import os
from copy import deepcopy
from unittest import mock
from unittest.mock import mock_open

import pytest
import yaml

from website_monitor.config_reader import read_config


@pytest.fixture
def env_vars():
    return {
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "db",
        "KAFKA_HOST": "localhost",
        "KAFKA_PORT": "9092",
        "KAFKA_TOPIC": "metrics"
    }


def format_config_data(config_data, env_vars):
    formatted_data = deepcopy(config_data)
    formatted_data["kafka"]["bootstrap_servers"] = formatted_data["kafka"]["bootstrap_servers"].format(
        KAFKA_HOST=env_vars["KAFKA_HOST"], KAFKA_PORT=env_vars["KAFKA_PORT"]
    )
    formatted_data["kafka"]["topic"] = formatted_data["kafka"]["topic"].format(
        KAFKA_TOPIC=env_vars["KAFKA_TOPIC"]
    )
    formatted_data["database"]["dsn"] = formatted_data["database"]["dsn"].format(
        POSTGRES_USER=env_vars["POSTGRES_USER"], POSTGRES_PASSWORD=env_vars["POSTGRES_PASSWORD"],
        POSTGRES_HOST=env_vars["POSTGRES_HOST"], POSTGRES_PORT=env_vars["POSTGRES_PORT"],
        POSTGRES_DB=env_vars["POSTGRES_DB"]
    )
    return formatted_data


def test_read_config_with_env_vars(env_vars):
    config_data = {
        "producer_interval": 15,
        "timeout": 10,
        "kafka": {
            "bootstrap_servers": "{KAFKA_HOST}:{KAFKA_PORT}",
            "topic": "{KAFKA_TOPIC}",
            "security_protocol": "PLAINTEXT"
        },
        "database": {
            "dsn": "postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        },
        "websites": [
            {"url": "https://google.com"},
            {"url": "https://lichess.org", "regexp": "Lichess is open source"}
        ]
    }

    formatted_data = format_config_data(config_data, env_vars)
    config_yaml = yaml.dump(formatted_data)
    m = mock_open(read_data=config_yaml)

    with mock.patch.dict(os.environ, env_vars), mock.patch("builtins.open", m):
        result = read_config("test.yml")

    assert result == formatted_data
