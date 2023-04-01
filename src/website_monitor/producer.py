import json
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from website_monitor.kafka_util import create_kafka_ssl_context


class MessageProducer(ABC):
    @abstractmethod
    async def send_message(self, topic, message):
        pass

    @abstractmethod
    async def close(self):
        pass


class KafkaProducer(MessageProducer, AIOKafkaProducer):
    def __init__(self, bootstrap_servers, security_protocol="PLAINTEXT", ssl_config=None):
        ssl_context = create_kafka_ssl_context(security_protocol, ssl_config)
        super().__init__(bootstrap_servers=bootstrap_servers, security_protocol=security_protocol,
                         ssl_context=ssl_context)

    async def send_message(self, topic, message):
        serialized_message = json.dumps(message).encode('utf-8')
        await self.send_and_wait(topic, serialized_message)

    async def close(self):
        await super().stop()

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(KafkaConnectionError)
    )
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()


class ProducerFactory:
    @staticmethod
    def get_producer(producer_type, bootstrap_servers, security_protocol="PLAINTEXT", ssl_config=None):
        if producer_type == 'kafka':
            return KafkaProducer(bootstrap_servers, security_protocol, ssl_config)
        else:
            raise ValueError(f"Unsupported producer type: {producer_type}")
