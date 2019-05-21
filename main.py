import sys

import requests
from bs4 import BeautifulSoup
import json

import ac_oo
import oss
import osr

from text_processing import text_cu, stop_words, word_freq, phrases_freq, relevancy
import nltk
from nltk.stem import WordNetLemmatizer

import save_to_db
import save_to_json

#----
# run scraper with list of urls to check for scraping
# - read urls from db
# - check with db if url has been updated since last time,
#   then run the scrape function on new urls &
#   add them to the db, else do nothing
#   maybe save the timestamp of latest sitemap checkup

#-- shape data up
def text_processing (article):
  corpus = '\n\n\n\n'.join([article['title'], article['abstract'], article['body']])
  words = text_cu(corpus)
  words = nltk.word_tokenize(words)

  #-- produces random syllabes
  # lemmatizer = WordNetLemmatizer()
  # words = [lemmatizer.lemmatize(word) for word in words]

  article['body-tokens'] = stop_words(words, article)
  article['body-words-length'] = len(article['body-tokens'])

  word_freq(article['body-tokens'], article)

  phrases_freq(article['body-tokens'], 2, article)
  phrases_freq(article['body-tokens'], 3, article)

  relevancy(article['word-freq'], article)

  print('text processing done...')
  return article


#-- main
def main(name):
  #-- get sitemap
  sitemap = {
    'ac': 'https://amateurcities.com/post-sitemap.xml',
    'oo': 'https://www.onlineopen.org/sitemap.xml',
    'os': 'http://hub.openset.nl/backend/wp-json',
    'osr': 'http://openset.nl/reader/pocket/api/get.php?type=root&id=root'
  }

  #-- open-set apis
  apis = {
    'sections': [
      {
        'type': 'project',
        'url': 'http://hub.openset.nl/backend/wp-json/wp/v2/project',
        'data': {}
      },
      {
        'type': 'expertinput',
        'url': 'http://hub.openset.nl/backend/wp-json/swp_api/search',
        'data': {}
      },
    ],
    'categories': {
      'type': 'categories',
      'url': 'http://hub.openset.nl/backend/wp-json/wp/v2/categories',
      'data': {}
    }
  }

  names = {
    'ac': 'amateurcities',
    'oo': 'online-open',
    'os': 'openset',
    'osr': 'openset-reader'
  }

  t_url = sitemap[name]
  r = requests.get(t_url)
  data = r.text

  #-- make dict with { <lastmod>: <url> }
  soup = BeautifulSoup(data, "lxml")

  url = []
  mod = []

  def sitemap (data, key, arr):
    for item in data.find_all(key):
      arr.append(item.text)

  sitemap(soup, 'loc', url)
  sitemap(soup, 'lastmod', mod)

  index = dict(zip(mod, url))

  #-- compare sitemap with db
  # for mod, url in index.items():
  #   if url is not in db.xx.url:
  #     if mod > db.xx.date
  #       → do scrape()

  #--- scraping + processing + saving
  with requests.Session() as s:
    print('scraping ✂︎')

    articles = []
    # article = {}

    #-- go through each link in sitemap
    # ac / oo
    if (name == 'ac' or name == 'oo'):
      for mod, url in index.items():
        article = {}

        # 1. scrape
        ac_oo.scraper(s, mod, url, names[name], article)

        articles.append(article)

      save_to_json.store(name, articles)

        # save_to_db.scrape(article)

        # if (name == 'ac'):
        #   pub = 'amateurcities'
        # else:
        #   pub: 'online-open'

        # article_bd = save_to_db.get_body(pub)

        # 2. process
        # try:
        #   article = text_processing(article)
        # except Exception as e:
        #   print('text-processing:', e)

        # articles.append(article)


      # 4. save to json-file
      # save_to_json.dump(name, articles)


    # os
    elif (name == 'os'):
      # feed `apis[item.data{}]` w/ data
      def getData(item):
        item['data'] = requests.get(item['url']).json()

      catdata = getData(apis['categories'])

      # 1. scrape
      for section in apis['sections']:
        getData(section)

        article = {}

        for item in section['data']:
          oss.scraper(section, item, apis, article)
          # save_to_db.scrape(article)
          articles.append(article)

        save_to_json.store(name, articles)

          # 2. process
          # try:
          #   article = text_processing(article)
          # except Exception as e:
          #   print(e)

          # articles.append(article)

      # 4. save to json-file
      # save_to_json.dump(name, articles)


    elif (name == 'osr'):
      data = requests.get('http://openset.nl/reader/pocket/api/get.php?type=root&id=root').json()
      obj = data['_pocketjoins']['map']

      index = []
      for item in obj:
        for entry in item['_pocketjoins']['map']:
          if (entry['publish'] == True):
            index.append(entry['_pocketindex'])

      # 1. scrape
      for slug in index:
        article = {}

        osr.scraper(s, slug, article)
        # save_to_db.scrape(article)

        articles.append(article)

      save_to_json.store(name, articles)

        # 2. process
        # try:
        #   article = text_processing(article)
        # except Exception as e:
        #   print(e)


        # articles.append(article)

      # 4. save to json-file
      # save_to_json.dump(name, articles)

if __name__ == '__main__':
  main(sys.argv[1])
