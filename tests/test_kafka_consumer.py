import os
from unittest.mock import AsyncMock, mock_open, patch, MagicMock

import pytest
import yaml

from kafka_consumer_to_postgres import create_website_metrics_table_if_not_exists, CREATE_TABLE_QUERY, read_config, \
    create_consumer_and_writer


@pytest.mark.asyncio
async def test_create_website_metrics_table_if_not_exists():
    db_writer = AsyncMock()

    await create_website_metrics_table_if_not_exists(db_writer)

    db_writer.execute.assert_called_once_with(CREATE_TABLE_QUERY)


def test_read_config():
    config_data = {"kafka": {"bootstrap_servers": "localhost:9092", "topic": "test"}}
    m = mock_open(read_data=yaml.dump(config_data))
    with patch("builtins.open", m):
        config = read_config("test.yml")
        assert config == config_data


@patch.dict(os.environ, {"POSTGRES_USER": "user", "POSTGRES_PASSWORD": "password"})
@patch("kafka_consumer_to_postgres.ConsumerFactory")
@patch("kafka_consumer_to_postgres.DatabaseWriterFactory")
def test_create_consumer_and_writer(mock_db_writer_factory, mock_consumer_factory):
    mock_db_writer = MagicMock()
    mock_consumer = MagicMock()

    mock_db_writer_factory.get_writer.return_value = mock_db_writer
    mock_consumer_factory.get_consumer.return_value = mock_consumer

    config = {
        "kafka": {"bootstrap_servers": "localhost:9092", "topic": "test-topic"},
        "database": {
            "dsn": "postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/testdb"
        },
    }

    consumer, db_writer = create_consumer_and_writer(config)

    assert consumer == mock_consumer
    assert db_writer == mock_db_writer
    mock_consumer_factory.get_consumer.assert_called_once_with(
        "kafka", "localhost:9092", "test-topic"
    )
    mock_db_writer_factory.get_writer.assert_called_once_with(
        "postgres", "postgresql://user:password@localhost:5432/testdb"
    )