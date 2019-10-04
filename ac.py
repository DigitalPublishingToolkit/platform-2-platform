#---- ac
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
  title = soup.find('title').text.replace(' - Amateur Cities', '')

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
      taglist.append(tag.get('content'))

    article['tags'] = taglist

  tags = soup.find_all(attrs={'property': 'article:tag'})
  get_tags(tags)

  #-- author
  def get_author(classpublisher):
    author = soup.find('p', class_=classpublisher)

    if author is not None:
      if len(author.contents) > 0:
        print('author.contents[0].text', author.contents[0].text)
        article['author'] = author.contents[0].text
    else:
      article['author'] = ''

  get_author('author-name')

  #-- copy
  body = soup.find('article')
  if body is None:
    body = soup.find('section')

  if body is not None:
    try:
      pp = body.find_all('p')
      copy = []
      for p in pp:
        copy.append(p.text)
      copy = "\n\n\n\n".join(copy)
      article['body'] = copy
    except Exception as e:
      print('body parser', e)

  #-- imgs
  img_urls = []
  for img in soup.select('img[class*="wp-post-image"]'):
    img_urls.append(img['src'])

  img_store = []
  #-- write imgs
  for url in img_urls:
    # https://stackoverflow.com/a/7253830
    fn = url.rsplit('/', 1)[-1]

    dir_path = './imgs/' + publisher
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)

    # https://stackoverflow.com/a/18043472
    r = requests.get(url, stream=True)
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
