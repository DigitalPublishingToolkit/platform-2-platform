import sys

import requests
from bs4 import BeautifulSoup
import ac_oo
import oss
import osr
from text_processing import text_cu, stop_words, pos, word_freq, phrases_freq, relevancy
import nltk
import save_to_db
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
articles = []

def main(name, articles):
  names = {'ac': 'amateurcities',
           'oo': 'online-open',
           'os': 'openset',
           'osr': 'openset-reader',
           'kk': 'kirby-kit'}

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
                          'data': {}}, {'type': 'expertinput',
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

    mod = [ciso8601.parse_datetime(mod).isoformat() for mod in mod]
    last_mod = dict(zip(mod, url))

    publisher = names[name]
    datb_mod = save_to_db.get_mod(publisher)
    print(datb_mod)

    #--- compare mod from db w/ mod from fresh scraping lookup
    # https://blog.softhints.com/python-compare-dictionary-keys-values/

    def scrape_lookup(datb_mod, last_mod, publisher):
      # check if db has records of this publisher
      if bool(datb_mod) is True:
        db_mod = set(datb_mod.keys())
        sc_mod = set(last_mod.keys())
        mod_diff = sc_mod.difference(db_mod)

        # https://stackoverflow.com/a/17665928
        def ts_diff(diff, main_list):
          y = [k for k in main_list if k not in diff]
          return {k: main_list[k] for k in main_list if k not in y}

        # diff b/t fresh scraped articles and db
        index_diff = ts_diff(mod_diff, last_mod)

        print('-- index-diff --')
        print(len(index_diff), index_diff)

        return index_diff
      else:
        print('db data for %s is still empty' % publisher)
        index_diff = last_mod
        return index_diff

    mod_list = scrape_lookup(datb_mod, last_mod, publisher)

    def add_to_db(nmod_diff, article, old_article):
      if len(list(datb_mod)) > 0:
        print('update db record')
        save_to_db.scrape_update(article, old_article)
      else:
        print('save to db')
        save_to_db.scrape(article)

    #--- scraping + processing + saving
    def scrape(name, publisher, mod_list, sitemap):
      with requests.Session() as s:
        print('scraping ✂︎')

        index = mod_list
        old_article = mod_list.values()
        nmod_diff = list(mod_list)

        # ac / oo
        if (name == 'ac' or name == 'oo' or name == 'kk'):
          for mod, url in index.items():
            article = {}
            ac_oo.scraper(s, mod, url, publisher, article)
            articles.append(article)

            add_to_db(nmod_diff, article, url)

        # os
        elif (name == 'os'):
          # feed `apis[item.data{}]` w/ data
          def getData(item):
            item['data'] = requests.get(item['url']).json()

          # catdata = getData(apis['categories'])
          for section in apis['sections']:
            getData(section)

            for item in section['data']:
              article = {}
              oss.scraper(section, item, apis, article)
              articles.append(article)

              add_to_db(nmod_diff, article, old_article)

        # osr
        elif (name == 'osr'):
          data = requests.get(sitemap['osr']).json()
          obj = data['_pocketjoins']['map']

          index = []
          for item in obj:
            for entry in item['_pocketjoins']['map']:
              if (entry['publish'] is True):
                index.append(entry['_pocketindex'])

          for slug in index:
            article = {}

            osr.scraper(s, slug, article)
            articles.append(article)

            add_to_db(nmod_diff, article, old_article)

    #-- scrape
    scrape(sys.argv[1], publisher, mod_list, sitemap)

  # 2. process
  elif (sys.argv[2] == 'tx'):
    article_bd = save_to_db.get_body(publisher)
    print(article_bd)

    # for item in data:
    #   try:
    #     article = text_processing(item)
    #     articles.append(article)
    #   except Exception as e:
    #     print('text-processing:', e)

    # try:
    #   article = text_processing(article_bd)
    # except Exception as e:
    #   print('text-processing:', e)

    # # 3. save to db
    # save_to_db.body(article)

    # for article in articles:
    #   print(article['word-freq'])
    #   print('---')

    # save_to_json.dump(name, articles)


if __name__ == '__main__':
  main(sys.argv[1], articles)
