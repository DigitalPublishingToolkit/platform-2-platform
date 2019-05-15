#---- ac / oo
import sys
from bs4 import BeautifulSoup

def scraper(s, mod, url, name, article):
  art = s.get(url, allow_redirects=False)
  print(url)

  soup = BeautifulSoup(art.text, 'lxml')

  #-- mod + url
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
  if (name == 'amateurcities'):
    section = soup.find(attrs={'property':'article:section'})
    if (section != None):
      section = section.get('content')
      article['section'] = section
    else:
      article['section'] = 'empty'

  #-- copy
  if (name == 'amateurcities'):
    body = soup.find('article')
  elif (name == 'online-open'):
    body = soup.find('div', id='text').select('.contentCluster')[0]

  if (body != None):
    pp = body.find_all('p')
    copy = []
    for p in pp:
      copy.append(p.text)
    copy = "\n\n\n\n".join(copy)
    article['body'] = copy
  else:
    article['body'] = None


  print('scraping done...')
  return article
