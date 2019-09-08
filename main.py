import sys
import requests
from bs4 import BeautifulSoup
import ac_oo
import oss
import osr
from text_processing import text_cu, stop_words, pos, word_freq, phrases_freq, relevancy
import nltk
import save_to_db
import save_to_json
import get_from_db
from datetime import timezone
import ciso8601

#----
# run scraper with list of urls to check for scraping
# - read urls from db
# - check with db if url has been updated since last time,
#   then run the scrape function on new urls &
#   add them to the db, else do nothing
#   maybe save the timestamp of latest sitemap checkup

#-- shape data up
def text_processing(article):
  corpus = '\n\n\n\n'.join([article['title'], article['abstract'],
                            article['body']])
  words = text_cu(corpus)
  words = nltk.word_tokenize(words)

  #-- produces random syllables
  # lemmatizer = WordNetLemmatizer()
  # words = [lemmatizer.lemmatize(word) for word in words]

  sw = stop_words(words, article)
  article['body-tokens'] = pos(sw, article)
  article['body-words-length'] = len(article['body-tokens'])

  word_freq(article['body-tokens'], article)

  phrases_freq(article['body-tokens'], 2, article)
  phrases_freq(article['body-tokens'], 3, article)

  relevancy(article['word-freq'], article)

  print('text processing done')
  print(article)

  return article


#-- main
articles_pre = []
articles_post = []

def main(name, articles_pre, articles_post):
  names = {'ac': 'amateurcities',
           'oo': 'online-open',
           'os': 'open-set',
           'osr': 'open-set-reader',
           'kk': 'kirby-kit'}

  publisher = names[name]

  if(sys.argv[2] == 'sc'):
    #-- get sitemap
    sitemap = {'ac': 'https://amateurcities.com/post-sitemap.xml',
               'oo': 'https://www.onlineopen.org/sitemap.xml',
               'os': 'http://hub.openset.nl/backend/wp-json',
               'osr': 'http://openset.nl/reader/pocket/api/get.php?type=root&id=root',
               'kk': 'http://kk.andrefincato.info/sitemap.xml'}

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
    soup = BeautifulSoup(data, "lxml")

    def get_sitemap(data, key, arr):
      for item in data.find_all(key):
        arr.append(item.text)

    url = []
    mod = []
    get_sitemap(soup, 'loc', url)
    get_sitemap(soup, 'lastmod', mod)

    # for online-open (and anyone else), let's force add a UTC timezone
    # at the end of the date-timestamp, so we can match the date-timestamp
    # coming from the postgresql db, which automatically at a UTC tz as well
    # (this means a `+00:00` after `2019-07-04T22:00:00`, therefore
    # all date-timestamp are now in the full isodate format of
    # `2019-07-04T22:00:00+00:00`
    mod = [ciso8601.parse_datetime(mod).astimezone(tz=timezone.utc).isoformat() for mod in mod]
    last_mod = dict(zip(mod, url))

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

    #--- scraping + processing + saving
    def scrape(name, publisher, mod_list, sitemap):
      with requests.Session() as s:

        # ac / oo
        if (name == 'ac' or name == 'oo' or name == 'kk'):
          for mod, url in mod_list['entries'].items():
            old_article = url
            article = {}
            ac_oo.scraper(s, mod, url, publisher, article)
            articles_pre.append(article)

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
              articles_pre.append(article)
              save_to_db.scrape(article)
          else:
            print('os: db is full, no new articles to fetch')

        # osr
        elif (name == 'osr'):
          # data = requests.get(sitemap['osr']).json()
          # obj = data['_pocketjoins']['map']

          def get_sitemap(path):
            slugs = []
            with open(path) as tsv:
              tsv = csv.reader(tsv, delimiter='\t')
              for row in tsv:
                slugs.append(row[1].split('/')[-1])

            return slugs

          slug_list = get_sitemap('store/open-set-articles.tsv')
          print(slug_list)

          # index = []
          # for item in obj:
          #   for entry in item['_pocketjoins']['map']:
          #     if (entry['publish'] is True):
          #       index.append(entry['_pocketindex'])

          if mod_list['count'] >= 0 and mod_list['action'] == 'add':
            # for slug in index:
            for slug in slug_list:
              article = {}
              osr.scraper(s, slug, article)
              articles_pre.append(article)
              save_to_db.scrape(article)
          else:
            print('osr: db is full, no new articles to fetch')

        else:
          print('mod_list empty: nothing to scrape')

    #-- scrape
    scrape(sys.argv[1], publisher, mod_list, sitemap)

  # 2. process
  elif (sys.argv[2] == 'tx'):
    articles = get_from_db.get_body(publisher)
    # print(articles)

    for item in articles:
      try:
        article = text_processing(item)
        articles_post.append(article)
      except Exception as e:
        print('text-processing:', e)

    # 3. save to db
    # save_to_db.body(article)

    # for article in articles:
    #   print(article['word-freq'])
    #   print('---')

    save_to_json.dump(name, articles)


if __name__ == '__main__':
  main(sys.argv[1], articles_pre, articles_post)
