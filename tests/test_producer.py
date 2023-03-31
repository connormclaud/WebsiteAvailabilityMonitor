import pytest
import json
from unittest.mock import AsyncMock, patch
from website_monitor.producer import MessageProducer, KafkaProducer, ProducerFactory

# Test data
test_topic = "test_topic"
test_message = {"key": "value"}
serialized_message = json.dumps(test_message).encode("utf-8")
bootstrap_servers = "localhost:9092"


def test_message_producer_abstract_methods():
    with pytest.raises(TypeError):
        MessageProducer()


@pytest.mark.asyncio
async def test_kafka_producer_send_message():
    with patch("website_monitor.producer.AIOKafkaProducer"):
        producer = KafkaProducer(bootstrap_servers)
        producer.send_and_wait = AsyncMock(return_value=None)

        await producer.send_message(test_topic, test_message)

        producer.send_and_wait.assert_called_once_with(test_topic, serialized_message)


@pytest.mark.asyncio
async def test_kafka_producer_close():
    with patch("website_monitor.producer.AIOKafkaProducer.stop", new_callable=AsyncMock) as mock_stop:
        producer = KafkaProducer(bootstrap_servers)

        await producer.close()

        mock_stop.assert_called_once()


@patch("website_monitor.producer.KafkaProducer", autospec=True)
def test_get_kafka_producer(mock_kafka_producer):
    producer = ProducerFactory.get_producer("kafka", bootstrap_servers)

    mock_kafka_producer.assert_called_once_with(bootstrap_servers)
    assert isinstance(producer, KafkaProducer)


def test_get_unsupported_producer():
    producer_type = "unsupported"

    with pytest.raises(ValueError) as exc_info:
        ProducerFactory.get_producer(producer_type, bootstrap_servers)

    assert str(exc_info.value) == f"Unsupported producer type: {producer_type}"
