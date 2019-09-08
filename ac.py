#---- ac
import ciso8601
from bs4 import BeautifulSoup

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

  print('scraping done...')
  return article
