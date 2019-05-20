import sys
import time

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

#----
# run scraper with list of urls to check for scraping
# - read urls from db
# - check with db if url has been updated since last time,
#   then run the scrape function on new urls &
#   add them to the db, else do nothing
#   maybe save the timestamp of latest sitemap checkup

#-- shape data up
def text_processing (article):
  words = text_cu(article['body'])
  words = nltk.word_tokenize(words)

  lemmatizer = WordNetLemmatizer()
  words = [lemmatizer.lemmatize(word) for word in words]

  stop_words(words, article)

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

    article = {}
    #-- go through each link in sitemap
    # ac / oo
    if (name == 'ac' or name == 'oo'):
      for mod, url in index.items():
        # 1. scrape
        ac_oo.scraper(s, mod, url, names[name], article)
        save_to_db.scrape(article)

        # 2. process
        try:
          article = text_processing(article)
        except Exception as e:
          print(e)

        # 3. save to db


    # os
    elif (name == 'os'):
      # feed `apis[item.data{}]` w/ data
      def getData(item):
        item['data'] = requests.get(item['url']).json()

      catdata = getData(apis['categories'])

      # 1. scrape
      for section in apis['sections']:
        getData(section)

        for item in section['data']:
          oss.scraper(section, item, apis, article)
          # print(article)
          save_to_db.scrape(article)

          # 2. process
          try:
            article = text_processing(article)
          except Exception as e:
            print(e)

          # 3. save to db


    elif (name == 'osr'):
      data = requests.get('http://openset.nl/reader/pocket/api/get.php?type=root&id=root').json()
      obj = data['_pocketjoins']['map']

      index = []
      for item in obj:
        for entry in item['_pocketjoins']['map']:
          if (entry['publish'] == True):
            index.append(entry['_pocketindex'])

      for slug in index:
        osr.scraper(s, slug, article)
        save_to_db.scrape(article)

        # 2. process
        try:
          article = text_processing(article)
        except Exception as e:
          print(e)

        # 3. save to db

if __name__ == '__main__':
  main(sys.argv[1])
