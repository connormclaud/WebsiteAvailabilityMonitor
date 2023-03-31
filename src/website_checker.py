import asyncio
import aiohttp
import re
import time
from typing import Optional
import yaml

from producer import ProducerFactory


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

            # TODO(vitali, 30.03.2023): add timestamp
            result = {
                "url": url,
                "response_time": response_time,
                "status_code": status_code,
                "content_check": content_matched,
            }
            return result
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return None


async def main(config, run_once=False):
    websites = config["websites"]
    interval = config["producer_interval"]
    bootstrap_servers = config["kafka"]["bootstrap_servers"]
    kafka_topic = config["kafka"]["topic"]

    producer = ProducerFactory.get_producer("kafka", bootstrap_servers)

    async with aiohttp.ClientSession() as session, producer:
        while True:
            tasks = [check_website(session, site["url"], site["regexp"] if "regexp" in site else None)
                     for site in websites]
            # TODO(vitali, 30.03.2023) add pools of checkers
            results = await asyncio.gather(*tasks)

            for result in results:
                if result:
                    print(result)
                    await producer.send_message(kafka_topic, result)

            await asyncio.sleep(interval)
            if run_once:
                break


if __name__ == '__main__':
    with open("config.yml", "r") as config_file:
        configuration = yaml.safe_load(config_file)

    asyncio.run(main(configuration))
