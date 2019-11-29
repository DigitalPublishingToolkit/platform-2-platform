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
  author = soup.find('p', class_='author-name')
  try:
    print('author', author)
    article['author'] = author.contents[0].text
  except Exception as e:
    print("can't find author here, try other location", e)
    author = soup.find('p', class_='title')
    print('author', author.find('a').text)
    article['author'] = author.find('a').text

  #-- copy
  body = soup.find('article')
  if body is None:
    body = soup.find('section')

  #-- links
  if body is not None:
    try:
      links = []

      for link in body.find_all('a', href=True):
        #-- the try / except is because i try to check if the parent element wrapping the <a href> has a class attribute:
        #-- if yes, filter out some classes and grab only from the rest
        #-- if not, don't bother and move on grab everything
        try:
          if link.parent['class'][0] not in ['prev-page', 'next-page', 'wp-caption']:
            links.append(link['href'])
            print('YES', link['href'], link.parent['class'][0], '\n')
        except Exception as e:
          links.append(link['href'])
          print('YES', link['href'], '\n')

      article['links'] = links

      refs = []
      try:
        for ref in body.find_all('sup'):
          rr = ref.span.text.strip()
          refs.append(rr)
      except Exception as e:
        print('no ref?', e)

      article['refs'] = refs

    except Exception as e:
      print('link parser', e)
  else:
    article['links'] = []
    article['refs'] = []

  #-- body
  if body is not None:
    try:
      copy = []
      try:
        intro = body.find('div', class_='col-6').find('p').text
        copy.append(intro)
        pp = body.find('div', class_='container-4').find_all('p')
        
        for p in pp:
          copy.append(p.text)
      except Exception as e:
        print('try other layout format (IMG)', e)
        pp = body.find('div', class_='col-3').find_all('p')[3:]
        # print(pp)
        for p in pp:
          print('DESC', p)
          copy.append(p.text)

      copy = "\n\n".join(copy)
      article['body'] = copy
    except Exception as e:
      print('body parser', e)
  else:
    article['body'] = ''

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
