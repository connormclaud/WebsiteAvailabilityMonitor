import asyncio
import aiohttp
import re
import time
from typing import Optional


async def check_website(session: aiohttp.ClientSession, url: str, regexp: Optional[str] = None) -> Optional[dict]:
    start_time = time.perf_counter()
    try:
        async with session.get(url) as response:
            response_time = time.perf_counter() - start_time
            status_code = response.status
            content = None

            if regexp and response.content_type == "text/html":
                text = await response.text()
                content = True if re.search(regexp, text) else False

            result = {
                "url": url,
                "response_time": response_time,
                "status_code": status_code,
                "content_check": content,
            }
            return result
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return None


async def main(config, run_once=False):
    websites = config["websites"]
    interval = config["kafka"]["producer_interval"]

    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [check_website(session, site["url"], site["regexp"] if "regexp" in site else None) for site in websites]
            results = await asyncio.gather(*tasks)

            for result in results:
                if result:
                    print(result)
            await asyncio.sleep(interval)
            if run_once:
                break

if __name__ == '__main__':
    import yaml
    with open("config.yml", "r") as config_file:
        config = yaml.safe_load(config_file)

    asyncio.run(main(config))


