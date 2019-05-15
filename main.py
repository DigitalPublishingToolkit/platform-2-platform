import sys
import time

import requests
from bs4 import BeautifulSoup
import json
import markdown

import acoo_scraper
import os_scraper
import osr_scraper

from text_processing import text_cu, stop_words, word_freq, phrases_freq, relevancy
import nltk
from nltk.stem import WordNetLemmatizer

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

#-- save data to db
def save (article):
  timestamp = time.strftime("%Y-%m-%d-%H%M%S")
  print(article)
  print('saving done...')

def main(name):
  #-- get sitemap
  sitemap = {
    'ac': 'https://amateurcities.com/post-sitemap.xml',
    'oo': 'https://www.onlineopen.org/sitemap.xml',
    'os': 'http://hub.openset.nl/backend/wp-json',
    'osr': 'http://openset.nl/reader/pocket/api/get.php?type=root&id=root'
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
        acoo_scraper.scraper(s, mod, url, names[name], article)

        # 2. process
        try:
          article = text_processing(article)
        except:
          print('article has no `body` field')

        # 3. save to db
        save(article)

    # os
    elif (t_url == 'os'):
      for item in apis['sections']:
        os_scraper.scraper(item)

if __name__ == '__main__':
  main(sys.argv[1])
