import json
import sys
import argparse
from pathlib import Path
from detik import Detik
import asyncio
import aiofiles


async def write_articles_async(results, indexes, date, output_dir):
    date = date.split("-")
    output_dir = Path(output_dir) / date[0] / date[1] / date[2]
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, article in enumerate(results):
        if article is None:
            continue
        async with aiofiles.open(output_dir / f"{indexes[i]}.json", mode='w') as f:
            await f.write(json.dumps(article, indent=4))


def write_articles(results, indexes, date, output_dir):
    date = date.split("-")
    output_dir = Path(output_dir) / date[0] / date[1] / date[2]
    output_dir.mkdir(parents=True, exist_ok=True)
    for i, article in enumerate(results):
        with open(output_dir / f"{indexes[i]}.json", "w") as f:
            json.dump(article, f, indent=4)


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
    parser.add_argument("-b", "--batch_size", type=int, required=False, default=10,
                        help="Batch size")
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
        from couchbase_detik import CouchBaseDetik
        couchbase = CouchBaseDetik(host=args.host, username=args.username, password=args.password)
    else:
        detik = Detik()
        if args.input is None:
            print("Please specify input file")
            sys.exit(1)
        import csv
        with open(args.input, "r") as f:
            reader = csv.reader(f)
            urls = []
            indexes = []
            for i, row in enumerate(reader):
                print(".", end="", file=sys.stderr, flush=True)
                if i%100 == 0 and i != 0:
                    print("", file=sys.stderr, flush=True)
                index = row[0]
                date = row[1]
                url = row[3]
                urls.append(url)
                indexes.append(index)
                if len(urls) == args.batch_size:
                    results = asyncio.run(detik.get_pages(urls=urls))
                    write_articles(results, indexes, date, args.output_dir)
                    # asyncio.run(write_articles_async(results, indexes, date, args.output_dir))
                    urls = []
                    indexes = []
            results = asyncio.run(detik.get_pages(urls=urls))
            write_articles(results, indexes, date, args.output_dir)
            # asyncio.run(write_articles_async(results, indexes, date, args.output_dir))
        print("Done", file=sys.stderr)


if __name__ == "__main__":
    main()