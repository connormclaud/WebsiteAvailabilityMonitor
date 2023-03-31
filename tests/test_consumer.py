import pytest
from unittest.mock import patch, AsyncMock
from website_monitor.consumer import MessageConsumer, KafkaConsumer, ConsumerFactory

# Test data
test_topic = "test_topic"
bootstrap_servers = "localhost:9092"


def test_message_consumer_abstract_methods():
    with pytest.raises(TypeError):
        MessageConsumer()


@pytest.mark.asyncio
async def test_kafka_consumer_close():
    with patch("website_monitor.consumer.AIOKafkaConsumer.stop", new_callable=AsyncMock) as mock_stop:
        consumer = KafkaConsumer(bootstrap_servers, test_topic)

        await consumer.close()

        mock_stop.assert_called_once()


@patch("website_monitor.consumer.KafkaConsumer", autospec=True)
def test_get_kafka_producer(mock_kafka_consumer):
    consumer_type = "kafka"

    consumer = ConsumerFactory.get_consumer(consumer_type, bootstrap_servers, test_topic)

    mock_kafka_consumer.assert_called_once_with(bootstrap_servers, test_topic)
    assert isinstance(consumer, KafkaConsumer)


def test_get_unsupported_consumer():
    consumer_type = "unsupported"

    with pytest.raises(ValueError) as exc_info:
        ConsumerFactory.get_consumer(consumer_type, bootstrap_servers, test_topic)

    assert str(exc_info.value) == f"Unsupported consumer type: {consumer_type}"