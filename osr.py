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

  article['title'] = entry['title'].replace('<\br>\n', '').replace('<br>', '')
  article['abstract'] = ''

  article['publisher'] = 'open-set-reader'

  def tags(path, title):
    taglist = []
    with open(path) as table:
      reader = csv.reader(table, delimiter=';')
      for row in reader:
        if row[1] == article['url']:
          taglist = row[2].lower().strip().split('\n')

    article['tags'] = taglist

  tags('store/open-set-articles.csv', article['title'])

  author = entry['author']
  # try:
  #   author = author.split('/')
  #   print(author)
  # except Exception as e:
  #   print(e)
  #   author = author.split('&')
  #   print(author)
  # except Exception as e:
  #   print(e)
  article['author'] = [author]
  print(author)

  copy = []
  img_urls = []
  links = []
  refs = []

  if entry['text'] is not None:
    try:
      for block in entry['text']:
        for k, v in block.items():
          #-- txt
          if (k == 'content'):
            rv = markdown.markdown(v)
            hv = BeautifulSoup(rv, 'lxml')
            copy.append(hv.text)

            #-- links
            for link in hv.find_all('a', href=True):
              print(link, '\n', link['href'], '\n')
              links.append(link.get('href'))

          #-- imgs
          elif (k == 'filename'):
            img_urls.append(v)

      copy = '\n\n'.join(copy)
      article['body'] = copy
      article['links'] = links
      article['refs'] = refs
    except Exception as e:
      print('body, link, ref parser', e)
  else:
    article['body'] = []
    article['links'] = []
    article['refs'] = []

  img_store = []
  #-- write imgs
  if len(img_urls) > 0:
    try:
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
    except Exception as e:
      print('img scraper', e)
  else:
    article['images'] = []

  print('scraping done...')
  return article
