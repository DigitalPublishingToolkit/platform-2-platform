import sys
import requests
from bs4 import BeautifulSoup
import json
import markdown

from acoo_scraper import ac_oo_scraper
import os_scraper
import osr_scraper

def scrapple (name):
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

  #-- TODO compare sitemap with db
  # for mod, url in index.items():
  #   if url is not in db.xx.url:
  #     if mod > db.xx.date
  #       → do scrape()

  #--- scraping
  with requests.Session() as s:
    print('scraping ✂︎')

    article = {}
    # go through each link in sitemap
    if (name == 'ac' or name == 'oo'):
      for mod, url in index.items():
        ac_oo_scraper(s, mod, url, names[name], article)

    elif (t_url == 'os'):
      for item in apis['sections']:
        os_scraper(item)


    #-- end
    print('scraping completed!!')
    return article
