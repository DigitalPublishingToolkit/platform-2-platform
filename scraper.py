import sys
import requests
from bs4 import BeautifulSoup
import pprint
import contractions
import nltk
from nltk.tag import pos_tag_sents
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk import ngrams, FreqDist
import re

import io
import csv

#-- get sitemap

sitemap = ['https://amateurcities.com/post-sitemap.xml', 'https://www.unstudio.com/sitemap.xml', 'https://www.onlineopen.org/sitemap.xml']

t_url = sys.argv[1]
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

with requests.Session() as s:
  print(t_url, sitemap[0])

  if (t_url == sitemap[0]):
    print('scraping ✂︎')
    name = 'amateurcities'

    output = io.StringIO()
    f = csv.writer(open('%s.csv' % name, 'w'))
    f.writerow(['mod', 'url', 'title', 'desc', 'tags', 'section', 'body', 'body-tokens'])
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    for mod, url in index.items():
      #-- if lastmod is newer than prev lastmod
      art = s.get(url)
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

      section = soup.find(attrs={'property':'article:section'})
      if (section != None):
        section = section.get('content')
        article['section'] = section

      body = soup.find('article')
      if (body != None):
        pp = soup.find_all('p')
        copy = []
        for p in pp:
            copy.append(p.text)
        copy = "".join(copy)
        article['body'] = copy

        cptk = nltk.word_tokenize(copy)
        cptg = nltk.pos_tag(cptk)
        article['body-tokens'] = cptg

        #-- add to csv only if article has body-text
        f.writerow([article['mod'], article['url'], article['title'], article['desc'], article['tag'], article['section'], article['copy'], article['body-tokens']])

  elif (t_url == sitemap[1]):
    #-- unstudio
    print('scraping ✂︎')
    name = 'unstudio'
      
    output = io.StringIO()
    f = csv.writer(open('%s.csv' % name, 'w'))
    f.writerow(['mod', 'url', 'title', 'tags', 'body', 'body-tokens'])
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    for mod, url in index.items():
      #-- if lastmod is newer than prev lastmod
      art = s.get(url, allow_redirects=False)
      soup = BeautifulSoup(art.text, 'lxml')

      #-- extract infos and make dict
      article = {}

      article['mod'] = mod
      article['url'] = url
      print(url)
 
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
          article['tag'] = ''

        #-- copy
        text = body.find('div', class_='block--text')
        if (text != None):
          pp = text.find_all('p')
          copy = []
          for p in pp:
              copy.append(p.text)
          copy = "".join(copy)
          article['body'] = copy

          cptk = nltk.word_tokenize(copy)
          cptg = nltk.pos_tag(cptk)
          article['body-tokens'] = cptg

          #-- add to csv only if article has body-text
          f.writerow([article['mod'], article['url'], article['title'], article['tag'], article['body'], article['body-tokens'], article['stop-words']])

  elif(t_url == sitemap[2]):
    print('scraping ✂︎')
    name = 'open'

    output = io.StringIO()
    f = csv.writer(open('%s.csv' % name, 'w'))
    f.writerow(['mod', 'url', 'title', 'desc', 'theme', 'author', 'date', 'body', 'body-tokens', 'stop-words'])
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

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
      article['desc'] = desc

      theme = soup.find('p', class_='theme')
      if (theme != None):
        article['theme'] = theme.text

      author = soup.find('p', class_='author')
      if (author != None):
        article['author'] = author.text

      date = soup.find('p', class_='date')
      if (date != None):
        date.span.replaceWith('')
        article['date'] = date.text

      #-- copy
      body = soup.find('div', id='text').select('.contentCluster')
      if (body != None):
        pp = soup.find_all('p')
        copy = []
        for p in pp:
            copy.append(p.text)
        copy = "\n".join(copy)
        article['body'] = copy

        #-- nltk

        # take out punctuation
        copy = re.sub(r'[^\w\s]', '', copy)
        copy = copy.lower()

        # expand to contraction form
        copy = contractions.fix(copy)

        # split into words
        words = nltk.word_tokenize(copy)
        article['body-tokens'] = words

        # word-frequency
        wordfreq = []
        wf = FreqDist(words)
        for word, freq in wf.most_common(100):
            wwf = word, freq
            print(wwf)
            wordfreq.append(wwf)

        # wtag = nltk.pos_tag(words)
        # article['body-tokens'] = wtag 

        # stopwords
        sw = set(stopwords.words('english'))

        stopws = []
        for w in words:
          if w in sw:
            stopws.append(w)

        article['stop-words'] = stopws
        
        #-- add to csv only if article has body-text
        f.writerow([article['mod'], article['url'], article['title'], article['desc'], article['theme'], article['author'], article['date'], article['body'], article['body-tokens'], article['stop-words']])

  # -- end 
  print('scraping completed!!')
