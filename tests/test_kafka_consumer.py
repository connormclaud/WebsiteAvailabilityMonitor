import datetime
import json
import os
from unittest.mock import AsyncMock, mock_open, patch, MagicMock

import pytest
import yaml

from kafka_consumer_to_postgres import create_website_metrics_table_if_not_exists, CREATE_TABLE_QUERY, read_config, \
    create_consumer_and_writer, process_messages, INSERT_QUERY_WITH_PARAMETERS


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
        "kafka": {"bootstrap_servers": "localhost:9092", "topic": "test-topic", "security_protocol": "PLAINTEXT",
                  "ssl": {}},
        "database": {
            "dsn": "postgresql://user:password@localhost:5432/testdb"
        },
    }

    consumer, db_writer = create_consumer_and_writer(config)

    assert consumer == mock_consumer
    assert db_writer == mock_db_writer
    mock_consumer_factory.get_consumer.assert_called_once_with(
        "kafka", "localhost:9092", "test-topic", 'PLAINTEXT', {}
    )
    mock_db_writer_factory.get_writer.assert_called_once_with(
        "postgres", "postgresql://user:password@localhost:5432/testdb"
    )


class MockAsyncIterator:
    def __init__(self, messages):
        self.messages = messages

    async def __aiter__(self):
        for msg in self.messages:
            yield msg


@pytest.fixture
def mock_consumer_and_writer():
    message_value = {
        "url": "https://example.com",
        "response_time": 0.5,
        "status_code": 200,
        "content_check": True,
        "timestamp": "2023-04-01T12:00:00"
    }
    message = MagicMock()
    message.value.decode.return_value = json.dumps(message_value)

    consumer = MagicMock()
    consumer.consume.return_value = MockAsyncIterator([message])

    db_writer = MagicMock()
    db_writer.execute = AsyncMock()
    return consumer, db_writer


@pytest.mark.asyncio
async def test_process_messages(mock_consumer_and_writer):
    consumer, db_writer = mock_consumer_and_writer
    await process_messages(consumer, db_writer)

    db_writer.execute.assert_called_once_with(
        INSERT_QUERY_WITH_PARAMETERS,
        "https://example.com",
        0.5,
        200,
        True,
        datetime.datetime.fromisoformat("2023-04-01T12:00:00")
    )
