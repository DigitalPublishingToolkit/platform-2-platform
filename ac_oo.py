#---- ac / oo
import ciso8601
from bs4 import BeautifulSoup

def scraper(s, mod, url, name, article):
  art = s.get(url, allow_redirects=False)
  print(url)

  soup = BeautifulSoup(art.text, 'lxml')

  #-- mod + url
  article['mod'] = ciso8601.parse_datetime(mod).isoformat()
  article['url'] = url

  #-- title
  if (name == 'online-open'):
    title = soup.find(attrs={'property': 'og:title'}).get('content')

  try:
    title = soup.find('title').text
  except AttributeError:
    title = soup.find('title')

  if title is not None:
    article['title'] = title

  #-- publisher
  article['publisher'] = name

  #-- abstract
  abstract = soup.find(attrs={'property': 'og:description'})
  if abstract is not None:
    article['abstract'] = abstract.get('content')
  else:
    article['abstract'] = ''

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
    tags = soup.find_all(attrs={'property': 'article:tag'})
    get_tags(tags)

  elif (name == 'online-open'):
    tags = soup.find(attrs={'name': 'keywords'}).get('content').split(',')
    get_tags(tags)
  elif (name == 'kirby-kit'):
    tags = soup.find('p', class_='note-tags tags')
    get_tags(tags)

  #-- author
  def get_author(classname):
    author = soup.find('p', class_=classname)

    if author is not None:
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
  elif (name == 'kirby-kit'):
    get_author('logo')

  #-- section / category
  if (name == 'amateurcities'):
    section = soup.find(attrs={'property': 'article:section'})
    if section is not None:
      section = section.get('content')
      article['section'] = section
    else:
      article['section'] = 'empty'

  #-- copy
  if (name == 'amateurcities'):
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
    else:
      article['body'] = ''

  elif (name == 'online-open'):
    body = soup.find('div', id='text').select('.contentCluster')

    if body is not None:
      try:
        pp = []
        for block in body:
          item = block.find_all('p')
          if item is not None:
            pp.append(item)

        copy = []
        for p in pp:
          for item in p:
            copy.append(item.text)
        copy = "\n\n\n\n".join(copy)
        article['body'] = copy
      except Exception as e:
        print('body parser', e)
    else:
      article['body'] = ''
  else:
    article['body'] = ''

  print('scraping done...')
  return article
