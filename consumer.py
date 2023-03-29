from abc import ABC, abstractmethod
from aiokafka import AIOKafkaConsumer


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
    def __init__(self, bootstrap_servers, topic):
        super().__init__(topic, bootstrap_servers=bootstrap_servers)

    async def start(self):
        await super().start()

    async def consume(self):
        async for msg in self:
            yield msg

    async def close(self):
        await super().stop()


class ConsumerFactory:
    @staticmethod
    def get_consumer(consumer_type, bootstrap_servers, topic):
        if consumer_type == 'kafka':
            return KafkaConsumer(bootstrap_servers, topic)
        else:
            raise ValueError(f"Unsupported consumer type: {consumer_type}")
