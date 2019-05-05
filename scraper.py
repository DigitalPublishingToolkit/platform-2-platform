import sys
import time
import requests
from bs4 import BeautifulSoup
import pprint

import nltk
from nltk.stem import WordNetLemmatizer

from text_processing import text_cu, stop_words, word_freq, phrases_freq, relevancy

import io
import csv

import json
import markdown

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

t_url = sitemap[sys.argv[1]]
r = requests.get(t_url)
data = r.text

#-- make dict with { <lastmod>: <url> }
soup = BeautifulSoup(data, "lxml")

url = []
mod = []

# add if to check if `lastmod` has changed from the value in the db

# un-studio, check if page has `.com/zh/` or `.com/en/`
for item in soup.find_all('loc'):
  url.append(item.text)

for item in soup.find_all('lastmod'):
  mod.append(item.text)

index = dict(zip(mod, url))
print(len(index))


#---- generic scraping function
def scraper(name, article, articles):
  print('scraping ✂︎')

  name = names[sys.argv[1]]
  print(name)

  #-- if lastmod is newer than prev lastmod
  art = s.get(url, allow_redirects=False)
  print(url)

  soup = BeautifulSoup(art.text, 'lxml')

  #-- extract infos and make dict
  article['mod'] = mod
  article['url'] = url

  #-- title
  if (name == 'online-open'):
    title = soup.find(attrs={'property':'og:title'}).get('content')

  try:
    title = soup.find('title').text
  except AttributeError:
    title = soup.find('title')

  if (title != None):
    article['title'] = title

  #-- publisher
  article['publisher'] = name

  #-- abstract
  abstract = soup.find(attrs={'property':'og:description'})
  if (abstract != None):
    article['abstract'] = abstract.get('content')

  #-- tags
  def get_tags(tags):
    taglist = []
    try:
      for tag in tags:
        try:
          taglist.append(tag.get('content'))
        except AttributeError:
          taglist.append(tag)
    except TypeError:
      try:
        taglist.append(tags.content)
      except AttributeError:
        taglist.append('')

    article['tags'] = taglist

  if (name == 'amateurcities'):
    tags = soup.find_all(attrs={'property':'article:tag'})
    get_tags(tags)

  elif (name == 'online-open'):
    tags = soup.find(attrs={'name':'keywords'}).get('content').split(',')
    get_tags(tags)

  #-- author
  def get_author(classname):
    author = soup.find('p', class_ = classname)

    if (author != None):
        if len(author.contents) > 0:
          article['author'] = author.contents[0].text
        else:
          article['author'] = author.contents
    else:
      article['author'] = 'empty'

  if (name == 'amateurcities'):
    get_author('author-name')
  elif (name == 'online-open'):
    get_author('author')

  #-- section / category
  # if (name == 'amateurcities'):
  #   section = soup.find(attrs={'property':'article:section'})
  #   if (section != None):
  #     section = section.get('content')
  #     article['section'] = section
  #   else:
  #     article['section'] = 'empty'

  #-- copy
  if (name == 'amateurcities'):
    body = soup.find('article')
  elif (name == 'online-open'):
    body = soup.find('div', id='text').select('.contentCluster')

  if (body != None):
    pp = body.find_all('p')
    copy = []
    for p in pp:
      copy.append(p.text)
    copy = "\n\n\n\n".join(copy)
    article['body'] = copy
  else:
    article['body'] = None

  # articles.append(article)

  print('scraping done...')
  #--- gone through all urls in sitemap


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


def save (article, articles):
  name = names[sys.argv[1]]
  timestamp = time.strftime("%Y-%m-%d-%H%M%S")
  filename = name + '_' + timestamp

  output = io.StringIO()

  f = csv.writer(open('dump/%s.csv' % filename, 'w'))
  f.writerow(['mod', 'url', 'title', 'publisher', 'abstract', 'tags', 'author', 'section', 'body', 'body-tokens', 'body-words-length', 'word-freq', '2-word phrases', '3-word phrases', 'relevancy'])
  writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

  f.writerow(article.values())

  with open('dump/%s.json' % filename, 'w') as fp:
    json.dump(articles, fp)

  print('saving done...')

# + + + + +


#-- scraping
with requests.Session() as s:

  articles = []
  article = {}

  # go through each link in sitemap
  for mod, url in index.items():
    # fetch data
    scraper(t_url, article, articles)

    # do text processing
    try:
      text_processing(article)
    except Exception:
      print('article has empty body field')

    # print('- - - - - -')
    # print(article)
    #-- do the saving here!

  # save(article, articles)
  # print(len(articles))


  #------------
  #--- open set
  if(t_url == sitemap['os']):

    apis = {
      'project': 'http://hub.openset.nl/backend/wp-json/wp/v2/project',
      'expert': 'http://hub.openset.nl/backend/wp-json/swp_api/search',
      'categories': 'http://hub.openset.nl/backend/wp-json/wp/v2/categories',
    }

    rproj = requests.get(apis['project'])
    projdata = rproj.json()

    rexps = requests.get(apis['expert'])
    expsdata = rexps.json()

    rcat = requests.get(apis['categories'])
    catdata = rcat.json()

    projects = []

    for project in projdata:
      article = {}

      article['mod'] = project['modified_gmt']
      article['url'] = 'http://hub.openset.nl/' + project['type'] + '/' + project['slug']
      print(article['url'])

      article['title'] = project['title']['rendered']
      article['abstract'] = 'None'

      # look up categories
      for cat in catdata:
        if(len(project['categories']) > 0):
          if (cat['id'] == project['categories'][0]):
            article['tags'] = cat['name']

      names = project['acf']['student_name']
      names = list(map(str.strip, names.split(',')))
      names = list(enumerate(names))

      authors = []
      for name in names:
        if (name[0] %2 == 0):
          authors.append(name[1])

      article['author'] = authors

      textual = []
      texts = project['acf']
      for k, v in texts.items():
        if 'textual' in k:
          textual.append(v)

      copy = []
      for text in textual:
        for block in text:
          for k, v in block.items():
            if k == 'text_content':
              copy.append(v)

      soup = []
      for p in copy:
        soup.append(BeautifulSoup(p, 'lxml'))

      body = []
      for p in soup:
        body.append(p.text)

      body = "\n".join(body)
      article['body'] = body


    for ex in expsdata:
      article = {}

      article['mod'] = ex['modified_gmt']
      article['url'] = 'http://hub.openset.nl/' + 'expertinput/' + ex['slug']
      print(article['url'])

      article['title'] = ex['title']['rendered']

      def getText(text):
        arr = []
        soup = BeautifulSoup(text, 'lxml')
        for p in soup:
          arr.append(p.text)

        arr = "\n".join(arr)
        return arr

      abstract = getText(ex['excerpt']['rendered'])

      article['abstract'] = abstract

      # look up categories
      for cat in catdata:
        if(len(ex['categories']) > 0):
          if (cat['id'] == ex['categories'][0]):
            article['tags'] = cat['name']

      # authors
      names = ex['acf']['student_name']
      names = list(map(str.strip, names.split(',')))
      names = list(enumerate(names))

      authors = []
      for name in names:
        if (name[0] %2 == 0):
          authors.append(name[1])

      article['author'] = authors

      #-- copy
      copy = getText(ex['content']['rendered'])
      article['body'] = copy


  elif(t_url == sitemap['osr']):
    osr = requests.get('http://openset.nl/reader/pocket/api/get.php?type=root&id=root')
    data = osr.json()

    obj = data['_pocketjoins']['map']

    index = []
    for item in obj:
      for entry in item['_pocketjoins']['map']:
        if (entry['publish'] == True):
          index.append(entry['_pocketindex'])

    articles = []
    for slug in index:
      art = s.get('http://openset.nl/reader/pocket/api/get.php?type=articles&id=' + slug)
      entry = art.json()
      print(slug)

      article = {}

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

      copy = "".join(copy)
      article['body'] = copy

  # -- end 
  print('scraping completed!!')
