#--- open-set
import requests
from bs4 import BeautifulSoup

def scraper(section, item, apis, article):
  article['mod'] = item['modified_gmt']
  article['url'] = 'http://hub.openset.nl/' + section['type'] + '/' + item['slug']
  print(article['url'])

  article['title'] = item['title']['rendered']

  #-- publisher
  article['publisher'] = 'open-set'

  #-- abstract
  def getText(text):
    arr = []
    soup = BeautifulSoup(text, 'lxml')
    for p in soup:
      arr.append(p.text)

    return "\n".join(arr)

  try:
    abstract = getText(item['excerpt']['rendered'])
    article['abstract'] = abstract
  except:
    article['abstract'] = 'None'

  #-- tags
  taglist = []
  for cat in apis['categories']['data']:
    if(len(item['categories']) > 0):
      if (cat['id'] == item['categories'][0]):
        taglist.append(cat['name'])

  article['tags'] = taglist

  #-- authors
  names = item['acf']['student_name']
  names = list(map(str.strip, names.split(',')))
  names = list(enumerate(names))

  authors = []
  for name in names:
    if (name[0] %2 == 0):
      authors.append(name[1])

  article['author'] = authors

  #-- copy
  def get_copy(data, key, arr):
    for k, v in data.items():
      if key in k:
        arr.append(v)

  try:
    article['body'] = getText(item['content']['rendered'])
  except:
    textual = []
    get_copy(item['acf'], 'textual', textual)

    copy = []
    for text in textual:
      for block in text:
        get_copy(block, 'text_content', copy)

    soup = []
    for p in copy:
      soup.append(BeautifulSoup(p, 'lxml'))

    body = []
    for p in soup:
      body.append(p.text)

    body = "\n".join(body)
    article['body'] = body


  print('scraping done...')
  return article
