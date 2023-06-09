from abc import ABC, abstractmethod

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from website_monitor.kafka_util import create_kafka_ssl_context


class MessageConsumer(ABC):
    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def consume(self):
        pass

    @abstractmethod
    async def close(self):
        pass


class KafkaConsumer(MessageConsumer, AIOKafkaConsumer):
    def __init__(self, bootstrap_servers, topic, security_protocol="PLAINTEXT", ssl_config=None):
        ssl_context = create_kafka_ssl_context(security_protocol, ssl_config)
        super().__init__(topic, bootstrap_servers=bootstrap_servers,
                         security_protocol=security_protocol, ssl_context=ssl_context)

    async def start(self):
        await AIOKafkaConsumer.start(self)

    async def consume(self):
        async for msg in self:
            yield msg

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


class ConsumerFactory:
    @staticmethod
    def get_consumer(consumer_type, bootstrap_servers, topic, security_protocol="PLAINTEXT", ssl_config=None):
        if consumer_type == 'kafka':
            return KafkaConsumer(bootstrap_servers, topic, security_protocol, ssl_config=ssl_config)
        else:
            raise ValueError(f"Unsupported consumer type: {consumer_type}")
