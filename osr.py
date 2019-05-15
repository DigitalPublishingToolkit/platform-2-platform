#---- open-set-reader
import json
import requests
import markdown
from bs4 import BeautifulSoup

def scraper(s, slug, article):
  art = s.get('http://openset.nl/reader/pocket/api/get.php?type=articles&id=' + slug)
  entry = art.json()
  print(slug)

  article['mod'] = 'empty'
  article['url'] = 'http://openset.nl/reader/#!/article/' + slug

  article['title'] = entry['title']
  article['abstract'] = 'empty'

  article['tags'] = 'empty'
  article['author'] = entry['author']

  copy = []
  for block in entry['text']:
    for k,v in block.items():
      if (k == 'content'):
        rv = markdown.markdown(v)
        hv = BeautifulSoup(rv, 'lxml')
        copy.append(hv.text)

  copy = ''.join(copy)
  article['body'] = copy

  # print(article)
  print('scraping done...')
  return article
