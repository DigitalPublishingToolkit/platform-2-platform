#---- ac / oo
import ciso8601
from bs4 import BeautifulSoup
import os
import requests
import shutil

def scraper(s, mod, url, publisher, article):
  art = s.get(url, allow_redirects=False)
  print(url)

  soup = BeautifulSoup(art.text, 'lxml')

  #-- mod + url
  article['mod'] = ciso8601.parse_datetime(mod).isoformat()
  article['url'] = url

  #-- title
  if (publisher == 'online-open'):
    title = soup.find(attrs={'property': 'og:title'}).get('content')

  if title is not None:
    article['title'] = title

  #-- publisher
  article['publisher'] = publisher

  #-- abstract
  abstract = soup.find(attrs={'property': 'og:description'})
  if abstract is not None:
    article['abstract'] = abstract.get('content')
  else:
    article['abstract'] = ''

  #-- tags
  def get_tags(tags):
    taglist = []
    for tag in tags:
      taglist.append(tag)

    article['tags'] = taglist

  tags = soup.find(attrs={'name': 'keywords'})
  if tags is not None:
    tags = tags.get('content').split(',')

  get_tags(tags)

  #-- author
  def get_author():
    author = soup.find(attrs={'name': 'author'})

    if author is not None:
      article['author'] = author.get('content')

  get_author()

  body = soup.find('div', id='text').select('.contentCluster')

  if body is not None:
    try:
      pp = []
      for block in body:
        item = block.find_all('p')
        if item is not None:
          pp.append(item)

      copy = []
      for p in pp:
        for item in p:
          copy.append(item.text)
      copy = "\n\n\n\n".join(copy)
      article['body'] = copy
    except Exception as e:
      print('body parser', e)
  else:
    article['body'] = ''

  #-- imgs
  img_urls = []
  for figure in soup.find_all('figure'):
    img_urls.append(figure.find('img')['src'])

  img_store = []
  #-- write imgs
  for url in img_urls:
    # https://stackoverflow.com/a/7253830
    fn = url.rsplit('/', 1)[-1]

    dir_path = './imgs/' + publisher
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)

    # https://stackoverflow.com/a/18043472
    full_url = 'https://www.onlineopen.org/' + url
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
