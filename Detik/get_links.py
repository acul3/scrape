import argparse
from detik import Detik


def main():
    """
    This function print out article links in csv format or save them to a couchbase database bucket.
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start_date", type=str, required=True,
                        help="Start date, i.e. 2019-01-10")
    parser.add_argument("-e", "--end_date", type=str, required=False,
                        help="End date (inclusive), i.e. 2019-01-20")
    parser.add_argument("-c", "--couchbase", required=False, action='store_true',
                        help="Store the links in couchbase")
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
        couchbase = None
    detik = Detik()
    article_links = detik.get_article_links(args.start_date, args.end_date)
    for i, article in enumerate(article_links):
        if args.couchbase:
            couchbase.upsert_document(article)
        else:
            title = article["title"].replace('"', '""')
            print(f'"{article["index"]}","{article["date"]}","{article["category"]}","{article["url"]}","{title}"')


if __name__ == '__main__':
    main()
