import asyncio
import yaml
import os
from consumer import ConsumerFactory
from db_writer import DatabaseWriterFactory


async def main(config):
    kafka_config = config["kafka"]
    db_config = config["database"]
    bootstrap_servers = kafka_config["bootstrap_servers"]
    topic = kafka_config["topic"]

    dsn = db_config["dsn"].format(
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"]
    )

    consumer = ConsumerFactory.get_consumer("kafka", bootstrap_servers, topic)
    db_writer = DatabaseWriterFactory.get_writer("postgres", dsn)

    async with consumer, db_writer:
        try:
            query = """
                INSERT INTO website_metrics (url, response_time, status_code, content_check)
                VALUES ($1, $2, $3, $4)
            """
            async for message in consumer.consume():
                print(f"Received message: {message}")

                await db_writer.write(query, message["url"], message["response_time"], message["status_code"],
                                      message["content_check"])
        except KeyboardInterrupt:
            print("Shutting down...")


if __name__ == "__main__":
    with open("config.yml", "r") as config_file:
        configuration = yaml.safe_load(config_file)

    asyncio.run(main(configuration))
