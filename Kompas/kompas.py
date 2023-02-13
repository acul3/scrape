import sys
import requests
import re
from bs4 import BeautifulSoup
import time
import datetime
import aiohttp
from aiohttp.client_exceptions import ServerDisconnectedError
import asyncio
import json
from json.decoder import JSONDecodeError
from pathlib import Path


class Kompas:
    headers = {
        'cache-control': 'max-age=0',
        'user-agent': 'Mozilla/5.0',
        'accept': 'text/html,application/xhtml+xml,application/xml',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en,en-US;q=0.9,id;q=0.8,de;q=0.7,ms;q=0.67'
    }
    categories = {
        "nasional": "https://{category}.kompas.com/search/{date}",
        "global": "https://www.kompas.com/{category}/search/{date}",
        "regional": "https://{category}.kompas.com/search/{date}",
        "health": "https://{category}.kompas.com/search/{date}",
        "edukasi": "https://{category}.kompas.com/search/{date}",
        "money": "https://{category}.kompas.com/search/{date}",
        "lifestyle": "https://{category}.kompas.com/search/{date}",
        "tekno": "https://{category}.kompas.com/search/{date}",
        "properti": "https://{category}.kompas.com/search/{date}",
        "bola": "https://{category}.kompas.com/search/{date}",
        "travel": "https://{category}.kompas.com/search/{date}",
        "otomotif": "https://{category}.kompas.com/search/{date}",
        "kolom": "https://{category}.kompas.com/search/{date}",
        "hype": "https://www.kompas.com/{category}/search/{date}",
    }
    kompas_wait = Path("/tmp/kompas_wait.txt")

    def __init__(self):
        pass

    @staticmethod
    def get_article_links(start_date, end_date):
        """
        Get all article links from Kompas website. The function returns a generator.
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
            for category in Kompas.categories:
                print(".", end="", file=sys.stderr, flush=True)
                date = f"{date_current.year}-{date_current.month:02d}-{date_current.day:02d}"
                url = Kompas.categories[category].format(category=category, date=date)
                try:
                    while True:
                        time_to_wait = 10
                        while True:
                            try:
                                req = requests.get(url, headers=Kompas.headers)
                                break
                            except requests.exceptions.ConnectionError:
                                # Sleep time_to_wait seconds before trying again
                                time.sleep(time_to_wait)
                                time_to_wait *= 1.5
                        if req.url != url or req.status_code == 401:
                            return None
                        page = BeautifulSoup(req.content, 'html.parser')
                        links = page.select("h3 .article__link")
                        for link in links:
                            index = re.sub(r".+/read/\d+/\d+/\d+/(\d+).+", r"\1", link["href"])
                            if index not in article_index:
                                article_index.add(index)
                                yield {
                                    "index": index,
                                    "url": link["href"],
                                    "title": link.text,
                                    "date": date,
                                    "category": category
                                }
                        next_page = page.select_one("a.paging__link--next:-soup-contains('Next')")
                        if next_page is not None:
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
        return Kompas.categories

    async def get_page(self, url, session):
        try:
            r = await session.request('GET', url=f"{url}?page=all", headers=self.headers)
        except Exception as e:
            print(f"{url} - {e}", file=sys.stderr, flush=True)
            return None
        if r.status != 200:
            return None
        try:
            data = await r.text()
            page = BeautifulSoup(data, 'html.parser')
            article = {}
            title = page.find_all('meta', attrs={'property': 'og:title'})
            article["title"] = title[0]["content"] if len(title) > 0 else ""
            article["title"] = re.sub(r" Halaman all.*", "", article["title"])
            article["url"] = url
            article["description"] = page.find_all('meta', attrs={'property': 'og:description'})[0]["content"]
            article["description"] = re.sub(r" Halaman all.*", "", article["description"])
            image_url = page.find_all('meta', attrs={'property': 'og:image'})
            article["image_url"] = image_url[0]["content"] if len(image_url) > 0 else ""
            if article["image_url"] == "":
                image_url = page.select("div.photo__wrap img")
                if len(image_url) > 0:
                    article["image_url"] = image_url[0]["src"]
            article["image_url"] = re.sub(r"crops.+(watermark\(.+\))?/data/photo", "data/photo", article["image_url"])  # Fix image url
            article["image_url"] = re.sub(r"\?.+", "", article["image_url"])
            article["image_caption"] = page.select("div.photo__caption")
            article["image_caption"] = article["image_caption"][0].next.strip() \
                if len(article["image_caption"]) > 0 else ""
            article["image_author"] = page.select("div.photo__caption span")
            article["image_author"] = article["image_author"][0].text.strip("( )") if len(article["image_author"]) > 0 else ""
            article["author"] = page.find_all('meta', attrs={'name': 'content_author'})
            article["author"] = article["author"][0]["content"] if len(article["author"]) > 0 else ""
            article["author_id"] = page.find_all('meta', attrs={'name': 'content_author_id'})
            article["author_id"] = article["author_id"][0]["content"] if len(article["author_id"]) > 0 else ""
            article["editor"] = page.find_all('meta', attrs={'name': 'content_editor'})
            article["editor"] = article["editor"][0]["content"] if len(article["editor"]) > 0 else ""
            article["editor_id"] = page.find_all('meta', attrs={'name': 'content_editor_id'})
            article["editor_id"] = article["editor_id"][0]["content"] if len(article["editor_id"]) > 0 else ""
            article["article_id"] = re.sub(r".+/read/(\d+/\d+/\d+/\d+)/.+", r"\1", article["url"])
            article["published_date"] = page.find_all('meta', attrs={'name': 'content_PublishedDate'})
            article["published_date"] = article["published_date"][0]["content"] if len(article["published_date"]) > 0 else ""
            article["keywords"] = page.find_all('meta', attrs={'name': 'content_tags'})
            article["keywords"] = article["keywords"][0]["content"] if len(article["keywords"]) > 0 else ""
            article["related_articles"] = []
            for url in page.select(".inner-link-baca-juga"):
                article["related_articles"].append(url["href"])

            content = page.select("div.read__content div.clearfix")
            if len(content) > 0:
                content = str(content[0])
            else:
                content = page.select("div.main-artikel-paragraf")
                content = str(content[0]) if len(content) > 0 else ""
            content = re.sub(r"<p><strong>Baca juga:.+</strong>", "", content)
            content = re.sub(r"<div id=\"EndOfArticle\".+", "", content, flags=re.DOTALL)
            content = re.sub(r"<div class=\"clearfix\">\n", "", content)
            content = BeautifulSoup(content, 'html.parser').text
            article['content'] = content.strip()
            return article
        except Exception as e:
            print(f"{url} - {e}", file=sys.stderr, flush=True)
            return None

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
                Path(Kompas.kompas_wait).touch()
                time.sleep(time_to_wait)
                time_to_wait = time_to_wait * 1.5
        return results
