import asyncio
from datetime import datetime
from typing import Iterable

import aiohttp
import colorama
from bs4 import BeautifulSoup

URLS = [
    "https://pypi.org",
    "https://python.org",
    "https://google.com",
    "https://amazon.com",
    "https://reddit.com",
    "https://stackoverflow.com",
    "https://ubuntu.com",
    "https://facebook.com",
    "https://www.microsoft.com",
    "https://www.ford.com",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
}


def get_title(html: str) -> str:
    soup = BeautifulSoup(html, 'lxml')
    return soup.title.string


async def download_page_title(url: str, session: aiohttp.ClientSession) -> str:
    async with session.get(url, headers=HEADERS) as response:
        from random import random
        if random() > 0.8:
            raise ValueError("bad")
        response.raise_for_status()
        html = await response.text()
        return get_title(html)


async def download_all_page_titles(urls: Iterable[str], loop: asyncio.AbstractEventLoop) -> None:
    async with aiohttp.ClientSession() as session:
        tasks = [download_page_title(url, session)
                 for url in urls]
        titles = await asyncio.gather(*tasks)
        for url, title in zip(urls, titles):
            print(f"Web page {url} has title: {title}")


def main() -> None:
    colorama.init()
    start_time = datetime.now()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(download_all_page_titles(URLS, loop))
    exec_time = (datetime.now() - start_time).total_seconds()
    print(colorama.Fore.GREEN + f"Summary: it took {exec_time:,.2f} seconds to run")


if __name__ == '__main__':
    main()
