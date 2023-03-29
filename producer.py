from abc import ABC, abstractmethod
import json
from aiokafka import AIOKafkaProducer


class MessageProducer(ABC):
    @abstractmethod
    async def send_message(self, topic, message):
        pass

    @abstractmethod
    async def close(self):
        pass


class KafkaProducer(MessageProducer, AIOKafkaProducer):
    def __init__(self, bootstrap_servers):
        AIOKafkaProducer.__init__(self, bootstrap_servers=bootstrap_servers)

    async def send_message(self, topic, message):
        serialized_message = json.dumps(message).encode('utf-8')
        await self.send_and_wait(topic, serialized_message)

    async def close(self):
        await super().stop()


class ProducerFactory:
    @staticmethod
    def get_producer(producer_type, bootstrap_servers):
        if producer_type == 'kafka':
            return KafkaProducer(bootstrap_servers)
        else:
            raise ValueError(f"Unsupported producer type: {producer_type}")