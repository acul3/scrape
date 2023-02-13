import json
import requests
import sys
import re
import argparse
from bs4 import BeautifulSoup
import time
from pathlib import Path


headers = {
    'cache-control': 'max-age=0',
    'user-agent': 'Mozilla/5.0',
    'accept': 'text/html,application/xhtml+xml,application/xml',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en,en-US;q=0.9,id;q=0.8,de;q=0.7,ms;q=0.67'
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start_date", type=str, required=False, default="2020-01-01",
                        help="Start date, i.e. 2019-01-10")
    parser.add_argument("-e", "--end_date", type=str, required=False,
                        help="End date (inclusive), i.e. 2019-01-20")
    parser.add_argument("-c", "--couchbase", required=False, action='store_true',
                        help="Store the links in couchbase")
    parser.add_argument("-i", "--input", type=str, required=False, default=None,
                        help="Input csv file")
    parser.add_argument("-o", "--output_dir", type=str, required=False, default="output",
                        help="Output directory")
    parser.add_argument("--host", type=str, required=False, default="localhost",
                        help="Hostname for couchbase")
    parser.add_argument("-u", "--username", type=str, required=False, default="user",
                        help="Username for couchbase")
    parser.add_argument("-p", "--password", type=str, required=False, default="password",
                        help="Password for couchbase")
    args = parser.parse_args()
    if args.end_date is None:
        args.end_date = args.start_date
    if args.couchbase:
        from couchbase_kompas import CouchBaseKompas
        couchbase = CouchBaseKompas(host=args.host, username=args.username, password=args.password)
    else:
        if args.input is None:
            print("Please specify input file")
            sys.exit(1)
        import csv
        meta_keys = [
            'title', 'url', 'content_category', 'content_subcategory', 'content_location',
            'content_author_id', 'content_author', 'content_editor_id', 'content_editor',
            'content_type', 'content_PublishedDate', 'content_tags'
        ]
        with open(args.input, "r") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                article = {}
                print(".", end="", file=sys.stderr, flush=True)
                if i%100 == 0 and i != 0:
                    print("", file=sys.stderr, flush=True)
                index = row[0]
                date = row[1]
                url = row[3]
                time_to_wait = 10
                while True:
                    try:
                        req = requests.get(url, headers=headers)
                        break
                    except requests.exceptions.ConnectionError:
                        # Sleep time_to_wait seconds before trying again
                        time.sleep(time_to_wait)
                        time_to_wait *= 1.5
                if req.url[req.url.find("://"):] != url[url.find("://"):] or req.status_code == 401:
                    continue
                page = BeautifulSoup(req.content, 'html.parser')
                script = str(page.select("head script")[0])
                script = re.sub(r"(.+push)\(({.+})\).+", r"\2", script, flags=re.DOTALL)
                meta_data = json.loads(script)
                for key in meta_keys:
                    if key in meta_data:
                        if type(meta_data[key]) == dict:
                            article[key] = meta_data[key]['0'].strip()
                        else:
                            article[key] = meta_data[key].strip()
                    else:
                        article[key] = ""
                content = str(page.select("div.read__content div.clearfix")[0])
                content = re.sub(r"<p><strong>Baca juga:.+</strong>", "", content)
                content = re.sub(r"<div id=\"EndOfArticle\".+", "", content, flags=re.DOTALL)
                content = re.sub(r"<div class=\"clearfix\">\n", "", content)
                content = BeautifulSoup(content, 'html.parser').text
                article['content'] = content
                date = date.split("-")
                output_dir = Path(args.output_dir)/date[0]/date[1]/date[2]
                output_dir.mkdir(parents=True, exist_ok=True)
                with open(output_dir/f"{index}.json", "w") as f:
                    json.dump(article, f, indent=4)

        couchbase = None


if __name__ == "__main__":
    main()