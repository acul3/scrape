import sys
import requests
import re
from bs4 import BeautifulSoup
import time
import datetime
from pathlib import Path
import asyncio
import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError
import json
from json.decoder import JSONDecodeError


class Detik:
    """
    Get all article links from Detik website. The function returns a generator.
    """
    headers = {
        'cache-control': 'max-age=0',
        'user-agent': 'Mozilla/5.0',
        'accept': 'text/html,application/xhtml+xml,application/xml',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,en-US;q=0.9,id;q=0.8,de;q=0.7,ms;q=0.67'
    }
    categories = {
        "news": "https://{category}.detik.com/indeks?date={date}",
        "finance": "https://{category}.detik.com/indeks?date={date}",
        "hot": "https://{category}.detik.com/indeks?date={date}",
        "sport": "https://{category}.detik.com/indeks?date={date}}",
        "oto": "https://{category}.detik.com/indeks?date={date}",
        "travel": "https://{category}.detik.com/indeks?date={date}",
        "food": "https://{category}.detik.com/indeks?date={date}",
        "health": "https://{category}.detik.com/indeks?date={date}",
        "edu": "https://www.detik.com/edu/indeks?date={date}",
    }
    meta_keys = [
        'title', 'url',
    ]
    detik_wait = Path("/tmp/detik_wait.txt")

    def __init__(self):
        pass

    @staticmethod
    def get_article_links(start_date, end_date):
        """
        Get all article links from Detik website. The function returns a generator.
        :param start_date:
        :param end_date:
        :return:
        """
        start = datetime.date(*[int(t) for t in start_date.split("-")])
        end = datetime.date(*[int(t) for t in end_date.split("-")])
        one_day = datetime.timedelta(days=1)
        date_current = start
        date_diff = end - date_current
        while date_diff.days >= 0:
            print(f"Download {date_current}", end=" ", file=sys.stderr, flush=True)
            article_index = set()
            for category in Detik.categories:
                print(".", end="", file=sys.stderr, flush=True)
                date = f"{date_current.month:02d}/{date_current.day:02d}/{date_current.year}"
                url = Detik.categories[category].format(category=category, date=date)
                try:
                    while True:
                        time_to_wait = 10
                        while True:
                            try:
                                req = requests.get(url, headers=Detik.headers)
                                break
                            except requests.exceptions.ConnectionError:
                                # Sleep time_to_wait seconds before trying again
                                time.sleep(time_to_wait)
                                time_to_wait *= 1.5
                        if req.url != url or req.status_code == 401:
                            return None
                        page = BeautifulSoup(req.content, 'html.parser')
                        links = page.select("h3.media__title a")
                        for link in links:
                            index = re.sub(r".+/d-(\d+)/.+", r"\1", link["href"])
                            if index not in article_index:
                                article_index.add(index)
                                yield {
                                    "index": index,
                                    "url": link["href"],
                                    "title": link.text,
                                    "date": f"{date_current.year}-{date_current.month:02d}-{date_current.day:02d}",
                                    "category": category
                                }
                        next_page = page.select_one("div.pagination a:-soup-contains('Next')")
                        if next_page is not None and next_page.get("href"):
                            url = next_page["href"]
                        else:
                            break

                except KeyError as ke:
                    print(ke)
                    return None
            date_current = date_current + one_day
            date_diff = end - date_current
            print("", file=sys.stderr, flush=True)

    @staticmethod
    def get_categories():
        return Detik.categories

    async def get_page(self, url, session):
        r = await session.request('GET', url=f"{url}", headers=self.headers)
        if r.status != 200:
            return None
        data = await r.text()
        page = BeautifulSoup(data, 'html.parser')
        article = {}
        article["title"] = page.find_all('meta', attrs={'property': 'og:title'})[0]["content"]
        article["url"] = page.find_all('meta', attrs={'property': 'og:url'})[0]["content"]
        article["description"] = page.find_all('meta', attrs={'property': 'og:description'})[0]["content"]
        article["image_url"] = page.find_all('meta', attrs={'property': 'og:image'})[0]["content"]
        article["image_url"] = re.sub(r"\?.+", "", article["image_url"])  # Fix image url
        # caption = page.select("figcaption.detail__media-caption")[0].text
        caption = page.select("figcaption")
        article["image_caption"] = ""
        article["image_author"] = ""
        if len(caption) > 0:
            caption = page.select("figcaption")[0].text
            caption = re.search(r"([^(]+) ?(\((.+)\))?", caption)
            if caption.group(3):
                article["image_caption"] = caption.group(1) if caption else ""
                article["image_author"] = caption.group(3) if caption else ""
            else:
                caption = caption.group(1).split(". ")
                article["image_caption"] = caption[0] if caption else ""
                article["image_author"] = caption[1] if len(caption) > 1 else ""
            article["author"] = page.find_all('meta', attrs={'name': 'author'})[0]["content"]
            try:
                article["article_id"] = page.find_all('meta', attrs={'name': 'articleid'})[0]["content"]
            except IndexError:
                article["article_id"] = ""
        article["published_date"] = page.find_all('meta', attrs={'name': 'publishdate'})[0]["content"]
        article["keywords"] = page.find_all('meta', attrs={'name': 'keywords'})[0]["content"]
        content = page.select("div.detail__body-text")[0].text
        article['content'] = content.strip()
        return article

    async def get_pages(self, urls):
        time_to_wait = 30
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    tasks = []
                    for url in urls:
                        tasks.append(self.get_page(url=url, session=session))
                    results = await asyncio.gather(*tasks, return_exceptions=False)
                    break
            except (JSONDecodeError, ServerDisconnectedError) as error:
                print("json error:", error)
                Path(Detik.detik_wait).touch()
                time.sleep(time_to_wait)
                time_to_wait = time_to_wait * 1.5
        return results
