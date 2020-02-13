from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Iterable, Tuple

import requests
from bs4 import BeautifulSoup
import colorama

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


def download_page_title(url: str, session: requests.Session) -> str:
    response = session.get(url, headers=HEADERS)
    title = get_title(response.text)
    return title


def download_all_page_titles(urls) -> Iterable[Tuple[str]]:
    with ThreadPoolExecutor(10) as pool:
        session = requests.Session()
        download_page_title_ = partial(download_page_title, session=session)
        result = pool.map(download_page_title_, URLS)
    return result


def main() -> None:
    colorama.init()
    start_time = datetime.now()
    for url, title in zip(URLS, download_all_page_titles(URLS)):
        print(f"Web page {url} has title: {title}")
    exec_time = (datetime.now() - start_time).total_seconds()
    print(colorama.Fore.GREEN + f"Summary: it took {exec_time:,.2f} seconds to run")


if __name__ == '__main__':
    main()
