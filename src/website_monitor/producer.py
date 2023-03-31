from abc import ABC, abstractmethod
import json
from aiokafka import AIOKafkaProducer
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from aiokafka.errors import KafkaConnectionError


class MessageProducer(ABC):
    @abstractmethod
    async def send_message(self, topic, message):
        pass

    @abstractmethod
    async def close(self):
        pass


class KafkaProducer(MessageProducer, AIOKafkaProducer):
    def __init__(self, bootstrap_servers):
        super().__init__(bootstrap_servers=bootstrap_servers)

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


class ProducerFactory:
    @staticmethod
    def get_producer(producer_type, bootstrap_servers):
        if producer_type == 'kafka':
            return KafkaProducer(bootstrap_servers)
        else:
            raise ValueError(f"Unsupported producer type: {producer_type}")