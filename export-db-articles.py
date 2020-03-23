import sys
from get_from_db import get_pub_articles
import save_to_json
import save_to_csv


def dump_articles(pub):
    articles = get_pub_articles(pub)
    save_to_json.dump(pub, articles)
    save_to_csv.dump(pub, articles)


dump_articles(sys.argv[1])
