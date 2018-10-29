import requests
from bs4 import BeautifulSoup
import redis
import nltk
from nltk.tag import pos_tag_sents

import io
import csv

db = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

#-- get sitemap

url = 'https://amateurcities.com/post-sitemap.xml'
url2 = 'https://www.unstudio.com/sitemap.xml'
r = requests.get(url)
data = r.text

#-- make dict with { <lastmod>: <url> }

soup = BeautifulSoup(data, "lxml")

url = []
mod = []

#-- add if to check if `lastmod` has 
#   changed from the value in the db

for item in soup.find_all('loc'):
  url.append(item.text)

for item in soup.find_all('lastmod'):
  mod.append(item.text)

index = dict(zip(mod, url))

db.hmset('sitemap', index)
print('--- ↓ db.sitemap ↓ ---')
print(db.hgetall('sitemap'))
print('--- ↑ db.sitemap ↑ ---')

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

  output = io.StringIO()
  f = csv.writer(open('dump.csv', 'w'))
  f.writerow(['mod', 'url', 'title', 'desc', 'tags', 'section', 'body', 'body-tokens'])
  writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

  for mod, url in index.items():
    #-- if lastmod is newer than prev lastmod
    art = s.get(url)
    soup = BeautifulSoup(art.text, 'lxml')

    #-- extract infos and make dict
    article = {}

    article['mod'] = mod
    #f.writerow([mod])
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

        f.writerow([mod, url, title, desc, tag, section, copy, cptg])
        
    #-- save to db
    db.hmset('entry', article)
    print('--- ↓ entry ↓ ---')
    print(db.hgetall('entry'))
    print('--- ↑ entry ↑ ---\n')


