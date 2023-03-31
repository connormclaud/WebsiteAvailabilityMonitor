import asyncio
import datetime
from asyncio import as_completed

import aiohttp
import re
import time
from typing import Optional, Dict
import yaml

from website_monitor.producer import ProducerFactory


async def check_website(session: aiohttp.ClientSession, url: str, regexp: Optional[str] = None) -> Optional[dict]:
    start_time = time.perf_counter()
    try:
        async with session.get(url) as response:
            response_time = time.perf_counter() - start_time
            status_code = response.status
            content_matched = None

            if regexp and response.content_type == "text/html":
                text = await response.text()
                content_matched = True if re.search(regexp, text) else False

            timestamp = datetime.datetime.utcnow().isoformat()
            result = {
                "url": url,
                "response_time": response_time,
                "status_code": status_code,
                "content_check": content_matched,
                "timestamp": timestamp,
            }
            return result
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return None


def read_config(config_file_path: str) -> Dict:
    with open(config_file_path, "r") as config_file:
        return yaml.safe_load(config_file)


async def process_task(future, timeout, producer, kafka_topic):
    try:
        result = await future
        if result:
            print(result)
            await producer.send_message(kafka_topic, result)
    except TimeoutError:
        print(f"Task timeout: task took longer than {timeout} seconds to complete.")
    except Exception as e:
        print(f"Error in task: {e}")


async def process_website_checks(tasks, timeout, producer, kafka_topic, task_manager):
    for future in task_manager(tasks, timeout=timeout):
        await process_task(future, timeout, producer, kafka_topic)


async def create_website_check_tasks(session, websites):
    return [check_website(session, site["url"], site["regexp"] if "regexp" in site else None)
            for site in websites]


async def main(config, run_once=False, producer_factory=ProducerFactory, client_session=None,
               task_manager=as_completed):
    websites = config["websites"]
    interval = config["producer_interval"]
    bootstrap_servers = config["kafka"]["bootstrap_servers"]
    kafka_topic = config["kafka"]["topic"]
    timeout = config["timeout"]

    producer = producer_factory.get_producer("kafka", bootstrap_servers)
    if not client_session:
        client_session = aiohttp.ClientSession()

    async with client_session as session, producer:
        while True:
            tasks = await create_website_check_tasks(session, websites)

            await process_website_checks(tasks, timeout, producer, kafka_topic, task_manager)

            await asyncio.sleep(interval)
            if run_once:
                break


if __name__ == '__main__':
    configuration = read_config("website_monitor/config.yml")
    asyncio.run(main(configuration))
