import os
import requests
import json
import re
from pathlib import Path
from tqdm import tqdm
import argparse
import logging


headers = {
    'authority': 'api.prod-api.storial.co',
    'authorization': 'Bearer XXX',  # Please change the XXX with your auth code, or set the env variable STORIAL_AUTH_CODE
    'cache-control': 'max-age=0',
    'user-agent': 'Mozilla/5.0',
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en,en-US;q=0.9,id;q=0.8,de;q=0.7,ms;q=0.67',
    'origin': 'https://storial.co',
    'referer': 'https://storial.co/'
}


class Book():
    book_list_api = "https://api.prod-api.storial.co/v2/book/list/?page={page}&sort=time"
    chapter_api = "https://api.prod-api.storial.co/v2.1/chapter/detail_by_url/?url={book_title}&chapter_index={chapter_index}"
    book_api = "https://api.prod-api.storial.co/v2/book/detail_by_url/?url={book_title}&sort=time"

    def __init__(self):
        pass

    @staticmethod
    def get_chapter(url: str):
        try:
            req = requests.get(url, headers=headers)
            if req.status_code == 401:
                print(req.reason)
                return None
            script = json.loads(req.content)
            chapter = {
                "chapter_name": script['data']['data']['chapter_detail']['chapter_name'],
                "total_real_hit": script['data']['data']['chapter_detail']['total_real_hit'],
                "total_vote_up": script['data']['data']['chapter_detail']['total_vote_up'],
                "chapter_content": script['data']['data']['chapter_detail']['chapter_content']
            }
            chapter["chapter_content"] = re.sub(r'<span class="wt">[^<]+</span>', '', chapter["chapter_content"])
            chapter["chapter_content"] = re.sub(r'<.?br[^>]*>', '\n', chapter["chapter_content"])
            chapter["chapter_content"] = re.sub(r'</p>', '\n', chapter["chapter_content"])
            chapter["chapter_content"] = re.sub(r'</div>', '\n', chapter["chapter_content"])
            chapter["chapter_content"] = re.sub(r'<[^>]+>', '', chapter["chapter_content"])
            chapter["chapter_content"] = re.sub(r'\n{3,}', '\n\n', chapter["chapter_content"])
            return chapter
        except KeyError as ke:
            print(ke)
            return None

    @staticmethod
    def get_book_overview(url: str):
        try:
            req = requests.get(url, headers=headers)
            if req.status_code == 401:
                print(req.reason)
                return None
            script = json.loads(req.content)
            if len(script['data']['data']['chapter_list']) == 0:
                return None
            book_overview = {
                "author_list": [author['member_name'] for author in script['data']['data']['author_list']],
                "book_detail": script['data']['data']['book_detail'],
                "category": script['data']['data']['category']['category_name'],
                "chapter_list": list(script['data']['data']['chapter_list'].keys())
            }
            return book_overview
        except KeyError as ke:
            print(ke)
            return None

    @staticmethod
    def get_book(book_title: str, output_dir="books"):
        books_dir = Path(f"{output_dir}/{book_title[0]}/{book_title}")
        if books_dir.exists():
            return
        book_url = Book.book_api.replace("{book_title}", book_title)
        book_overview = Book.get_book_overview(book_url)
        if book_overview is None:
            return
        books_dir.mkdir(parents=True, exist_ok=True)
        with open(books_dir/f"book.json", "w") as book_file:
            json.dump(book_overview, book_file)
            for i, chapter_index in enumerate(tqdm(book_overview["chapter_list"],
                                                   total=len(book_overview["chapter_list"]))):
                with open(books_dir/f"chapter_{i+1:03}.json", "w") as chapter_file:
                    chapter_url = Book.chapter_api.replace("{book_title}", book_title).replace("{chapter_index}", chapter_index)
                    chapter = Book.get_chapter(chapter_url)
                    if chapter is not None:
                        json.dump(chapter, chapter_file)

    @staticmethod
    def get_book_list(max_total_pages=-1):
        page = 1
        book_list_url = Book.book_list_api.replace("{page}", str(page))
        req = requests.get(book_list_url, headers=headers)
        script = json.loads(req.content)
        book_paging = script["data"]["book_paging"]
        book_list = []
        book_list += script["data"]["book_list"]
        if max_total_pages == -1:
            max_total_pages = book_paging["total_pages"]
        for page in tqdm(range(book_paging["total_pages"]), total=min(book_paging["total_pages"], max_total_pages)):
            if page == 0:
                continue
            if page == max_total_pages:
                break
            book_list_url = Book.book_list_api.replace("{page}", str(page+1))
            req = requests.get(book_list_url, headers=headers)
            script = json.loads(req.content)
            book_list += script["data"]["book_list"]
        return book_list

    @staticmethod
    def get_book_list_by_category(category, max_total_pages=-1):
        page = 1
        book_list_url = Book.book_list_api.replace("{page}", str(page))
        book_list_url += f"&type=category&key={category}"
        req = requests.get(book_list_url, headers=headers)
        script = json.loads(req.content)
        book_paging = script["data"]["book_paging"]
        book_list = []
        book_list += script["data"]["book_list"]
        if max_total_pages == -1:
            max_total_pages = book_paging["total_pages"]
        for page in tqdm(range(book_paging["total_pages"]), total=min(book_paging["total_pages"], max_total_pages)):
            if page == 0:
                continue
            if page == max_total_pages:
                break
            book_list_url = Book.book_list_api.replace("{page}", str(page+1))
            book_list_url += f"&type=category&key={category}"
            req = requests.get(book_list_url, headers=headers)
            script = json.loads(req.content)
            book_list += script["data"]["book_list"]
        return book_list

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_dir", type=str, required=False, default="books",
                        help="Output directory where the books will be stored")
    parser.add_argument("--book_list", type=str, required=False, default="book_list",
                        help="The name of book list")
    parser.add_argument("--get_book_list", action='store_true',
                        help="Get book list")
    parser.add_argument("--get_book_list_by_category", type=str, required=False,
                        help="Get book list by category")
    parser.add_argument("--get_title", type=str, required=False,
                        help="Get a book with the title as argument")
    parser.add_argument("--get_books", required=False, action='store_true',
                        help="Get books using the index from the book_list.json or book_list_<category>.json")
    parser.add_argument("--start", type=int, required=False, default=0,
                        help="The starting index for --get_books")
    parser.add_argument("--end", type=int, required=False, default=-1,
                        help="The end index for --get_books")
    parser.add_argument("--min_total_user_read", type=int, required=False, default=10,
                        help="The minimum number of users read the book for --get_books")
    parser.add_argument("--min_rate_score", type=int, required=False, default=-1,
                        help="The minimum rate score of the book for --get_books")
    parser.add_argument("-q", "--quite", required=False, action='store_true',
                        help="Quite message")
    parser.add_argument("-d", "--debug", required=False, action='store_true',
                        help="Enable debug messages")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quite:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO)

    auth_code = os.getenv('STORIAL_AUTH_CODE')
    if auth_code is not None:
        headers["authorization"] = f'Bearer {auth_code}'
    book = Book()
    output_dir = args.output_dir
    books_dir = Path(f"{output_dir}")
    books_dir.mkdir(parents=True, exist_ok=True)
    if args.get_title is not None:
        book.get_book(args.get_title)
    elif args.get_books:
        # read the book list from json file
        book_list = json.load(open(books_dir/f"{args.book_list}.json", "r"))
        index_start = args.start
        if args.end == -1:
            index_end = len(book_list)
        else:
            index_end = args.end

        for i, story in enumerate(book_list[index_start:index_end]):
            if story["total_chapter"] == 0 \
                    or int(story["total_user_read"]) <= args.min_total_user_read \
                    or float(story["rate_score"]) <= args.min_rate_score:
                continue
            print(f"{index_start+i}/{index_end} Get book: {story['book_url']}")
            book.get_book(story["book_url"])
    elif args.get_book_list:
        # retrieve the book list from storial and save it as json file
        book_list = book.get_book_list()
        print(f"Number of books: {len(book_list)}")
        json.dump(book_list, open(books_dir/"book_list.json", "w"))
    elif args.get_book_list_by_category:
        # retrieve the book list by category from storial and save it as json file
        category = args.get_book_list_by_category
        book_list = book.get_book_list_by_category(category)
        print(f"Number of books: {len(book_list)}")
        json.dump(book_list, open(books_dir/f"book_list_{category}.json", "w"))


if __name__ == '__main__':
    main()

