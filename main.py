import sys
import requests
from bs4 import BeautifulSoup
import ac
import oo
import oss
import osr
import text_processing
import save_to_db
import get_from_db
from datetime import timezone, timedelta
import ciso8601
import csv
from collections import Counter
import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


# ---------------------------------------------------
# run scraper with list of urls to check for scraping
# - read urls from db
# - check with db if url has been updated since last time,
#   then run the scrape function on new urls &
#   add them to the db, else do nothing
#   maybe save the timestamp of latest sitemap checkup

#-- main
articles = []

def main(name, articles):
  names = {'ac': 'amateur-cities',
           'oo': 'online-open',
           'os': 'open-set',
           'osr': 'open-set-reader'}

  publisher = names[name]

  # ----------------------
  # 1. scraping
  if(sys.argv[2] == 'sc'):
    #-- get sitemap
    sitemap = {'ac': 'https://amateurcities.com/post-sitemap.xml',
               'oo': 'https://onlineopen.org/sitemap.xml',
               'os': 'http://hub.openset.nl/backend/wp-json',
               'osr': 'http://openset.nl/reader/pocket/api/get.php?type=root&id=root'}

    #-- open-set apis
    apis = {'sections': [{'type': 'project',
                          'url': 'http://hub.openset.nl/backend/wp-json/wp/v2/project',
                          'data': {}},
                         {'type': 'expertinput',
                          'url': 'http://hub.openset.nl/backend/wp-json/swp_api/search',
                          'data': {}}, ],
            'categories': {'type': 'categories',
                           'url': 'http://hub.openset.nl/backend/wp-json/wp/v2/categories',
                           'data': {}}}

    t_url = sitemap[name]
    r = requests.get(t_url)
    data = r.text

    #-- make dict with { <lastmod>: <url> }
    sm = BeautifulSoup(data, "lxml")

    sm_index = []
    for item in sm.find_all('url'):
      url = item.find('loc')
      ts = item.find('lastmod')
      if ts is not None:
        entry = (ts.text, url.text)
        sm_index.append(entry)

    # url = []
    # mod = []

    # for online-open (and anyone else), let's force add a UTC timezone
    # at the end of the date-timestamp, so we can match the date-timestamp
    # coming from the postgresql db, which automatically at a UTC tz as well
    # (this means a `+00:00` after `2019-07-04T22:00:00`, therefore
    # all date-timestamp are now in the full isodate format of
    # `2019-07-04T22:00:00+00:00`
    # mod = [ciso8601.parse_datetime(mod).astimezone(tz=timezone.utc).isoformat() for mod in mod]

    mod_t = []
    c = Counter()
    for item in sm_index:
      item_y = ciso8601.parse_datetime(item[0]).astimezone(tz=timezone.utc).isoformat()
      if item_y in mod_t:
        c.update({item_y: 1})
        print(c)

        item = ciso8601.parse_datetime(item[0]).astimezone(tz=timezone.utc)
        # <https://stackoverflow.com/a/100345>
        # use c = Counter to *monotonically* increase the timestamp of <modlast> items with only the date, by 1 sec each time
        tt = item + timedelta(0,c[item_y])
        t = tt.isoformat()
        mod_t.append(t)
      else:
        t = ciso8601.parse_datetime(item[0]).astimezone(tz=timezone.utc).isoformat()
        mod_t.append(t)

    url = [x[1] for x in sm_index]
    last_mod = dict(zip(mod_t, url))
    print('LASTMOD', last_mod)

    datb_mod = get_from_db.get_mod(publisher)

    #--- compare mod from db w/ mod from fresh scraping lookup
    # https://blog.softhints.com/python-compare-dictionary-keys-values/

    def scrape_lookup(datb_mod, last_mod, publisher):
      # check if db has records of this publisher
      index_diff = {}
      if bool(datb_mod) is True:
        db_mod = set(datb_mod.keys())
        sc_mod = set(last_mod.keys())
        mod_diff = sc_mod.difference(db_mod)

        # https://stackoverflow.com/a/17665928
        def ts_diff(diff, main_list):
          y = [k for k in main_list if k not in diff]
          return {k: main_list[k] for k in main_list if k not in y}

        # diff b/t fresh scraped articles and db
        index_diff['action'] = 'update'
        index_diff['entries'] = ts_diff(mod_diff, last_mod)
        index_diff['count'] = len(index_diff['entries'])

        print('-- index-diff --')
        print(index_diff)

        return index_diff
      else:
        print('db data for %s is still empty' % publisher)
        index_diff['action'] = 'add'
        index_diff['entries'] = last_mod
        index_diff['count'] = len(index_diff['entries'])
        return index_diff

    # this is the index_diff b/t db articles and online www
    mod_list = scrape_lookup(datb_mod, last_mod, publisher)

    def add_to_db(mod_list_count, mod_list_action, article, old_article):
      # check mod_list['action'] type to pick between
      # `scrape_update` & `scrape`
      if mod_list_count >= 0 and mod_list_action == 'update':
        print('update db record')
        save_to_db.scrape_update(article, old_article)
      else:
        print('save to db')
        save_to_db.scrape(article)

    #--- scraping + saving
    def scrape(name, publisher, mod_list, sitemap):
      with requests.Session() as s:

        # ac
        if (name == 'ac'):
          for mod, url in mod_list['entries'].items():
            old_article = url
            article = {}
            ac.scraper(s, mod, url, publisher, article)
            articles.append(article)

            add_to_db(mod_list['count'], mod_list['action'], article, old_article)

        # oo
        elif (name == 'oo'):
          for mod, url in mod_list['entries'].items():
            old_article = url
            article = {}
            oo.scraper(s, mod, url, publisher, article)
            articles.append(article)

            add_to_db(mod_list['count'], mod_list['action'], article, old_article)

        # ---
        # not using `add_to_db` function for os and osr
        # just checking if articles are saved in db once
        # after that no more scraping;
        # for os no more articles, for osr some new articles
        # will be manually added to db

        # os
        elif (name == 'os'):
          # feed `apis[item.data{}]` w/ data
          def getData(item):
            item['data'] = requests.get(item['url']).json()

          # fetch data for sections items and categories
          for section in apis['sections']:
            getData(section)

          getData(apis['categories'])

          if mod_list['count'] >= 0 and mod_list['action'] == 'add':
            for item in section['data']:
              article = {}
              oss.scraper(section, item, apis, article)
              articles.append(article)
              save_to_db.scrape(article)
          else:
            print('os: db is full, no new articles to fetch')

        # osr
        elif (name == 'osr'):
          def get_sitemap(path):
            slugs = []
            with open(path) as table:
              reader = csv.reader(table, delimiter=';')
              for row in reader:
                slugs.append(row[1].split('/')[-1])

            return slugs

          slug_list = get_sitemap("store/open-set-articles.csv")
          print(slug_list)

          if mod_list['count'] >= 0 and mod_list['action'] == 'add':
            for slug in slug_list:
              article = {}
              osr.scraper(s, slug, article)
              articles.append(article)
              save_to_db.scrape(article)
          else:
            print('osr: db is full, no new articles to fetch')

        else:
          print('mod_list empty: nothing to scrape')

    #-- do the scraping
    scrape(sys.argv[1], publisher, mod_list, sitemap)

  # ------------------
  # 2. text-processing
  elif (sys.argv[2] == 'tx'):
    articles = get_from_db.get_body(publisher)

    for item in articles:
      try:
        article_metadata = {}
        metadata = text_processing.process_metadata(item, article_metadata, publisher)
        save_to_db.metadata(metadata)
      except Exception as e:
        print('text-processing ERROR:', e)

  # ------------------
  # 3. text-tokenization
  elif (sys.argv[2] == 'tk'):
    articles = get_from_db.get_body(publisher)

    for item in articles:
      try:
        article_tokens = {}
        article_tk = {}

        text_processing.process_tokens(item, article_tk)

        article_tokens['title'] = item['title']
        article_tokens['author'] = item['author']
        article_tokens['publisher'] = item['publisher']
        article_tokens['word_freq'] = article_tk['word_freq']
        article_tokens['2-word_freq'] = article_tk['2-word_freq']
        article_tokens['3-word_freq'] = article_tk['3-word_freq']
        article_tokens['tokens'] = article_tk

        save_to_db.tokens(article_tokens)

      except Exception as e:
        print('text-processing ERROR:', e)

  # -------------------
  # 4. send suggestions
  elif (sys.argv[2] == 'tv'):
    print('tv')
    # ask.ask()


if __name__ == '__main__':
  main(sys.argv[1], articles)
