#--- open-set

import requests
from bs4 import BeautifulSoup

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

def getData(item):
  item['data'] = requests.get(item['url']).json()

for item in apis['sections']:
  getData(item)


# open-set scraper
# ----------------
def scraper(section):
  article = {}

  for item in section['data']:
    article['mod'] = item['modified_gmt']
    article['url'] = 'http://hub.openset.nl/' + section['type'] + '/' + item['slug']
    print(article['url'])

    article['title'] = item['title']['rendered']

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

    #-- categories
    for cat in apis['categories']['data']:
      if(len(item['categories']) > 0):
        if (cat['id'] == item['categories'][0]):
          article['tags'] = cat['name']

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

    #--- return
    ## return article ??
