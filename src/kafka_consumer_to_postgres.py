import asyncio
import datetime
import json
import os

import yaml

from website_monitor.consumer import ConsumerFactory
from website_monitor.db_writer import DatabaseWriterFactory


def read_config(file_path):
    with open(file_path, "r") as config_file:
        return yaml.safe_load(config_file)


def create_consumer_and_writer(config):
    kafka_config = config["kafka"]
    db_config = config["database"]
    bootstrap_servers = kafka_config["bootstrap_servers"]
    topic = kafka_config["topic"]

    dsn = db_config["dsn"].format(
        POSTGRES_USER=os.environ["POSTGRES_USER"],
        POSTGRES_PASSWORD=os.environ["POSTGRES_PASSWORD"]
    )

    consumer = ConsumerFactory.get_consumer("kafka", bootstrap_servers, topic)
    db_writer = DatabaseWriterFactory.get_writer("postgres", dsn)

    return consumer, db_writer


async def process_messages(consumer, db_writer):
    query = """
        INSERT INTO website_metrics (url, response_time, status_code, content_check, timestamp)
        VALUES ($1, $2, $3, $4, $5)
    """
    async for message in consumer.consume():
        print(f"Received message: {message}")
        metric = json.loads(message.value.decode("utf-8"))
        timestamp = datetime.datetime.fromisoformat(metric["timestamp"])
        await db_writer.execute(query, metric["url"], metric["response_time"], metric["status_code"],
                                metric["content_check"], timestamp)


async def create_website_metrics_table_if_not_exists(db_writer):
    create_table_query = """
        CREATE TABLE IF NOT EXISTS website_metrics (
            id SERIAL PRIMARY KEY,
            url TEXT NOT NULL,
            response_time DOUBLE PRECISION NOT NULL,
            status_code INTEGER NOT NULL,
            content_check BOOLEAN,
            timestamp TIMESTAMP NOT NULL
        );
    """
    await db_writer.execute(create_table_query)


async def main(config):
    consumer, db_writer = create_consumer_and_writer(config)
    print("Connecting to Kafka and Postgres...")
    async with consumer, db_writer:
        try:
            await create_website_metrics_table_if_not_exists(db_writer)
            await process_messages(consumer, db_writer)
        except KeyboardInterrupt:
            print("Shutting down...")


if __name__ == "__main__":
    configuration = read_config("website_monitor/config.yml")
    asyncio.run(main(configuration))