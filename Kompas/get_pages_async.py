import json
import sys
import argparse
from pathlib import Path
from kompas import Kompas
import asyncio


def write_articles(results, indexes, dates, output_dir):
    for i, article in enumerate(results):
        date = dates[i].split("-")
        date_dir = Path(output_dir) / date[0] / date[1] / date[2]
        date_dir.mkdir(parents=True, exist_ok=True)
        if article is None:
            continue
        with open(date_dir / f"{indexes[i]}.json", "w") as f:
            json.dump(article, f, indent=4)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start_date", type=str, required=False, default="1900-01-01",
                        help="Start date, i.e. 2019-01-10")
    parser.add_argument("-e", "--end_date", type=str, required=False, default="2100-12-31",
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
    if args.couchbase:
        from couchbase_kompas import CouchBaseKompas
        couchbase = CouchBaseKompas(host=args.host, username=args.username, password=args.password)
    else:
        kompas = Kompas()
        if args.input is None:
            print("Please specify input file")
            sys.exit(1)
        import csv
        with open(args.input, "r") as f:
            reader = csv.reader(f)
            urls = []
            indexes = []
            dates = []
            print(f"{args.start_date}: ", end="", file=sys.stderr, flush=True)
            counter = 0
            last_date = args.start_date
            for i, row in enumerate(reader):
                index = row[0]
                date = row[1]
                url = row[3]
                try:
                    _ = int(index)
                except ValueError:
                    continue
                if args.start_date <= date <= args.end_date:
                    print(".", end="", file=sys.stderr, flush=True)
                    if (last_date != date) or (counter % 100 == 0 and counter != 0):
                        if last_date != date:
                            counter = -1
                        print(f"\n{date}: ", end="", file=sys.stderr, flush=True)
                    last_date = date
                    counter += 1
                    urls.append(url)
                    indexes.append(index)
                    dates.append(date)
                    if len(urls) == args.batch_size:
                        results = asyncio.run(kompas.get_pages(urls=urls))
                        write_articles(results, indexes, dates, args.output_dir)
                        urls = []
                        indexes = []
                        dates = []
            results = asyncio.run(kompas.get_pages(urls=urls))
            write_articles(results, indexes, dates, args.output_dir)
        print("Done", file=sys.stderr)


if __name__ == "__main__":
    main()