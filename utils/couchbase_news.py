import re
from datetime import timedelta
# needed for any cluster connection
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
# needed for options -- cluster, timeout, SQL++ (N1QL) query, etc.
from couchbase.options import (ClusterOptions, ClusterTimeoutOptions,
                               QueryOptions)


class CouchBaseDetik():
    def __init__(self, host="localhost", username="user", password="password", bucket_name="news"):
        self.authenticator = PasswordAuthenticator(username, password)
        self.cluster = Cluster(f'couchbase://{host}', ClusterOptions(self.authenticator))
        self.cluster.wait_until_ready(timedelta(seconds=5))
        self.bucket = self.cluster.bucket(bucket_name)
        self.collection = self.bucket.default_collection()

    def upsert_document(self, key, doc):
        # print("\nUpsert CAS: ")
        try:
            result = self.collection.upsert(key, doc)
            # print(result.cas)
        except Exception as e:
            print(e)
            print(doc["url"])

    def insert_document(self, key, doc):
        # print("\nUpsert CAS: ")
        try:
            result = self.collection.insert(key, doc)
            # print(result.cas)
        except Exception as e:
            print(e)
            print(doc["url"])

    def get_news_by_key(self, key):
        # print("\nGet Result: ")
        try:
            result = self.collection.get(key)
            #print(result.content_as[str])
            return result.content_as[dict]
        except Exception as e:
            print(e)

    def select_news(self, query):
        print("\nLookup Result: ")
        try:
            sql_query = query
            row_iter = self.cluster.query(
                sql_query,
                QueryOptions(positional_parameters=[]))
            for row in row_iter:
                print(row)
        except Exception as e:
            print(e)