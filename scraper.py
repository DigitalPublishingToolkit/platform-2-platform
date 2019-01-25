import sys
import time
import requests
from bs4 import BeautifulSoup
import pprint
import contractions
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk import ngrams, FreqDist
import re

import io
import csv

import json

#-- get sitemap

sitemap = {
  'ac': 'https://amateurcities.com/post-sitemap.xml',
  'un': 'https://www.unstudio.com/sitemap.xml',
  'oo': 'https://www.onlineopen.org/sitemap.xml',
  'os': 'http://hub.openset.nl/backend/wp-json'
}

t_url = sitemap[sys.argv[1]]
r = requests.get(t_url)
data = r.text

#-- make dict with { <lastmod>: <url> }
soup = BeautifulSoup(data, "lxml")

url = []
mod = []

#-- add if to check if `lastmod` has 
#   changed from the value in the db

# un-studio, check if page has
# `.com/zh/` or `.com/en/`
for item in soup.find_all('loc'):
  url.append(item.text)

for item in soup.find_all('lastmod'):
  mod.append(item.text)

index = dict(zip(mod, url))
print(len(index))

pp = pprint.PrettyPrinter(indent=2)
# pp.pprint(index)

#-- fetch all pages and save them in the db
# ['<lastmod>': {
#   title: <title>,
#   url: <url>,
#   date: <date>,
#   author: <author>,
#   tags: [<tag>, <tag>, <tag>],
#   body: [<p>, <p>, <bq>]
# }]

# + + + + + + + + + + + + +
#-- text processing w/ nltk

#-- text-clean-up
def text_cu (text):
  # take out punctuation
  text = re.sub(r'[^\w\s]', '', text)
  text = text.lower()

  # expand to contraction form
  text = contractions.fix(text)

  return text

#-- stop-words
def stop_words (text):
  sw = set(stopwords.words('english'))

  stop_words = []
  wordsclean = []
  for w in text:
    if w in sw:
      stop_words.append(w)
    else:
      wordsclean.append(w)

  article['body-tokens'] = wordsclean
  # article['stop-words'] = stop_words

#-- word-frequency
def word_freq (text):
  wordfreq = []
  wf = FreqDist(text)
  for word, freq in wf.most_common():
    wwf = word, freq
    wordfreq.append(wwf)

  article['word-freq'] = wordfreq

#-- n-word phrases frequency
def phrases_freq (text, size):
  pf = dict()
  pf = FreqDist(ngrams(text, size))

  article[str(size) + 'w-phrases'] = pf.most_common()

# + + + + +
#-- scraping
with requests.Session() as s:
  if (t_url == sitemap['ac']):
    print('scraping ✂︎')
    name = 'amateurcities'
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    filename = name + '_' + timestamp

    output = io.StringIO()
    f = csv.writer(open('dump/%s.csv' % filename, 'w'))
    f.writerow(['mod', 'url', 'title', 'desc', 'tags', 'section', 'body', 'body-tokens', 'word-freq' , '2-word phrases', '3-word phrases'])
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    articles = []

    for mod, url in index.items():
      #-- if lastmod is newer than prev lastmod
      art = s.get(url)
      print(url)
      soup = BeautifulSoup(art.text, 'lxml')

      #-- extract infos and make dict
      article = {}

      article['mod'] = mod
      article['url'] = url

      title = soup.find('title').text
      article['title'] = title

      desc = soup.find(attrs={'property':'og:description'}).get('content')
      article['desc'] = desc

      tag = soup.find(attrs={'property':'article:tag'})
      if (tag != None):
        tag = tag.get('content')
        article['tag'] = tag
      else:
        article['tag'] = 'empty'

      section = soup.find(attrs={'property':'article:section'})
      if (section != None):
        section = section.get('content')
        article['section'] = section
      else:
        article['section'] = 'empty'

      #-- copy
      body = soup.find('article')
      if (body != None):
        pp = soup.find_all('p')
        copy = []
        for p in pp:
          copy.append(p.text)
        copy = "".join(copy)
        article['body'] = copy

        words = text_cu(copy)

        #-- tokenize & lemmatize
        words = nltk.word_tokenize(words)
        lemmatizer = WordNetLemmatizer()
        words = [lemmatizer.lemmatize(word) for word in words]

        stop_words(words)

        word_freq(article['body-tokens'])

        phrases_freq(article['body-tokens'], 2)
        phrases_freq(article['body-tokens'], 3)

        #-- add to csv only if article has body-text
        f.writerow(article.values())

        articles.append(article)

    with open('dump/%s.json' % filename, 'w') as fp:
      json.dump(articles, fp)


  elif (t_url == sitemap['un']):
    #-- unstudio
    print('scraping ✂︎')
    name = 'unstudio'
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    filename = name + '_' + timestamp

    output = io.StringIO()
    f = csv.writer(open('dump/%s.csv' % filename, 'w'))
    f.writerow(['mod', 'url', 'title', 'tags', 'body', 'body-tokens', 'word-freq', '2-word phrases', '3-word phrases'])
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    articles = []

    for mod, url in index.items():
      #-- if lastmod is newer than prev lastmod
      art = s.get(url, allow_redirects=False)
      print(url)
      soup = BeautifulSoup(art.text, 'lxml')

      #-- extract infos and make dict
      article = {}

      article['mod'] = mod
      article['url'] = url

      title = soup.find('title')
      if (title != None):
        article['title'] = title.text

      # seems to be always empty by checking 4-5 articles
      # desc = soup.find(attrs={'property':'og:description'}).get('content')
      # article['desc'] = desc

      body = soup.find('article')
      if (body != None):
        #-- tag 
        tag = body.find('div', class_='page-text__keyword')
        if (tag != None):
          tag = tag.text
          article['tag'] = tag
        else:
          article['tag'] = 'empty'

        #-- copy
        text = body.find('div', class_='block--text')
        if (text != None):
          pp = text.find_all('p')
          copy = []
          for p in pp:
              copy.append(p.text)
          copy = "".join(copy)
          article['body'] = copy

          words = text_cu(copy)

          #-- tokenize & lemmatize
          words = nltk.word_tokenize(words)
          lemmatizer = WordNetLemmatizer()
          words = [lemmatizer.lemmatize(word) for word in words]

          stop_words(words)

          word_freq(article['body-tokens'])

          phrases_freq(article['body-tokens'], 2)
          phrases_freq(article['body-tokens'], 3)

          articles.append(article)

          #-- add to csv only if article has body-text
          f.writerow(article.values())

      with open('dump/%s.json' % filename, 'w') as fp:
        json.dump(articles, fp)


  elif(t_url == sitemap['oo']):
    print('scraping ✂︎')
    name = 'open'
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    filename = name + '_' + timestamp

    output = io.StringIO()
    f = csv.writer(open('dump/%s.csv' % filename, 'w'))
    f.writerow(['mod', 'url', 'title', 'desc', 'tags', 'author', 'body', 'body-tokens', 'word-freq' , '2-word phrases', '3-word phrases'])
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    articles = []

    for mod, url in index.items():
      #-- if lastmod is newer than prev lastmod
      art = s.get(url)
      print(url)
      soup = BeautifulSoup(art.text, 'lxml')

      #-- extract infos and make dict
      article = {}

      article['mod'] = mod
      article['url'] = url

      title = soup.find(attrs={'property':'og:title'}).get('content')
      article['title'] = title

      desc = soup.find(attrs={'property':'og:description'}).get('content')
      desclist = []
      article['desc'] = desc

      tags = soup.find(attrs={'name':'keywords'}).get('content').split(',')
      if (tags != None):
        taglist = []
        for tag in tags:
          taglist.append(tag)

        article['tags'] = taglist
      else:
        article['tags'] = 'empty'

      author = soup.find('p', class_='author')
      if (author != None):
        article['author'] = author.text
      else:
        article['author'] = 'empty'

      #-- copy
      body = soup.find('div', id='text').select('.contentCluster')
      if (body != None):
        pp = []
        for block in body:
          item = block.find_all('p')
          if (item != None):
            pp.append(item)

        copy = []

        for p in pp:
          for item in p:
            copy.append(item.text)
        copy = "\n".join(copy)
        article['body'] = copy

        words = text_cu(copy)

        #-- tokenize & lemmatize
        words = nltk.word_tokenize(words)
        lemmatizer = WordNetLemmatizer()
        words = [lemmatizer.lemmatize(word) for word in words]

        stop_words(words)

        word_freq(article['body-tokens'])

        phrases_freq(article['body-tokens'], 2)
        phrases_freq(article['body-tokens'], 3)

        #-- add to csv only if article has body-text
        f.writerow(article.values())

        articles.append(article)

    with open('dump/%s.json' % filename, 'w') as fp:
        json.dump(articles, fp)

  elif(t_url == sitemap['os']):
    print('scraping ✂︎')
    name = 'openset'
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    filename = name + '_' + timestamp

    apis = {
      'project': 'http://hub.openset.nl/backend/wp-json/wp/v2/project',
      'expert': 'http://hub.openset.nl/backend/wp-json/swp_api/search',
      'categories': 'http://hub.openset.nl/backend/wp-json/wp/v2/categories',
    }

    rproj = requests.get(apis['project'])
    projdata = rproj.json()

    rcat = requests.get(apis['categories'])
    catdata = rcat.json()

    projects = []

    for project in projdata:
      article = {}

      article['mod'] = project['modified_gmt']
      article['url'] = 'http://hub.openset.nl/' + project['type'] + '/' + project['slug']
      print(article['url'])

      article['title'] = project['title']['rendered']

      # look up categories
      for cat in catdata:
        if (cat['id'] == project['categories'][0]):
          article['tags'] = cat['name']

      # names = project['acf']['student_name']
      # authors = list(map(str.strip, names.split(',')))
      # authors = list(filter(authors[i] for i in 1 == 0, authors))
      # print(authors)
      # article['author'] = authors

      # add to articles
      projects.append(article)

    #-- write to json file
    with open('%s.json' % filename, 'w') as fp:
      json.dump(projects, fp)

  # -- end 
  print('scraping completed!!')
