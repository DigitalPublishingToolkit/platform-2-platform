import requests
from bs4 import BeautifulSoup
import redis

db = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

#-- get sitemap

url = 'https://amateurcities.com/post-sitemap.xml'
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
# print('--- ↓ db.sitemap ↓ ---')
# print(db.hgetall('sitemap'))
# print('--- ↑ db.sitemap ↑ ---')

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
  for mod, url in index.items():
    #-- if lastmod is newer than prev lastmod
    article = s.get(url)
    soup = BeautifulSoup(article.text, 'lxml')

    #-- extract infos and make dict
    article = {}

    article['mod'] = mod
    article['url'] = url
    
    title = soup.find('title').text
    article['title'] = title
    #print('title= ' + title)

    desc = soup.find(attrs={'property':'og:description'}).get('content')
    article['desc'] = desc
    #print('desc= ' + desc)

    tag = soup.find(attrs={'property':'article:tag'})
    if (tag != None):
        tag = tag.get('content')
        article['tag'] = tag
        #print('tags= ' + tag) 

    section = soup.find(attrs={'property':'article:section'})
    if (section != None):
        section = section.get('content')
        article['section'] = section
        #print('section= ' + section + '\n\n') 
 
    #-- save to db
    db.hmset('entry', article)
    print('--- ↓ entry ↓ ---')
    print(db.hgetall('entry'))
    print('--- ↑ entry ↑ ---\n')


