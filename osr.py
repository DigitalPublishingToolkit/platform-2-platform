#---- open-set-reader
from datetime import datetime, timezone
import markdown
from bs4 import BeautifulSoup
import csv
import os
import requests
import shutil

def scraper(s, slug, article):
  art = s.get('http://openset.nl/reader/pocket/api/get.php?type=articles&id=' + slug)
  entry = art.json()
  # scheme 2016-04-14T21:11:06+00:00
  article['mod'] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
  article['url'] = 'http://openset.nl/reader/#!/article/' + slug

  article['title'] = entry['title'].replace('<\br>\n', '')
  article['abstract'] = ''

  article['publisher'] = 'open-set-reader'

  def tags(path, title):
    taglist = []
    with open(path) as tsv:
      tsv = csv.reader(tsv, delimiter='\t')

      for row in tsv:
        if row[0] == title:
          taglist = row[2].lower().strip().split('\n')

    article['tags'] = taglist

  tags('store/open-set-articles.tsv', article['title'])

  article['author'] = entry['author'].strip()

  copy = []
  img_urls = []
  links = []
  for block in entry['text']:
    for k, v in block.items():
      if (k == 'content'):
        rv = markdown.markdown(v)
        hv = BeautifulSoup(rv, 'lxml')
        copy.append(hv.text)

        #-- links
        for link in hv.find_all('a', href=True):
          print(link, '\n', link['href'], '\n')
          links.append(link.get('href'))

      elif (k == 'filename'):
        img_urls.append(v)

  copy = ''.join(copy)
  article['body'] = copy
  article['links'] = links

  img_store = []
  #-- write imgs
  for url in img_urls:
    dir_path = './imgs/open-set-reader'
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)

    # https://stackoverflow.com/a/18043472
    full_url = 'http://openset.nl/reader/pocket/uploads/' + url

    fn = url.replace('/', '-').replace('.', '-').replace(' ', '-')
    r = requests.get(full_url, stream=True)
    if not os.path.exists(dir_path + '/' + fn):
      with open(dir_path + '/' + fn, 'wb') as outf:
        shutil.copyfileobj(r.raw, outf)
      del r
    else:
      print('image already exists!', dir_path + '/' + fn)

    img_store.append(dir_path + '/' + fn)

  article['images'] = img_store

  print('scraping done...')
  return article
