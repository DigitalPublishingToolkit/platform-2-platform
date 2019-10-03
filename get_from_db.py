import psycopg2
from psycopg2.extras import register_composite
from config import config
from collections import namedtuple

#-- utils

#-- from `[('mod',), ...]` to `['mod', ...]`
def get_flat_list(data):
  flat_list = [l[0] for l in data]
  return flat_list

def get_labels(cur, table):
  cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = '%s';" % (table,))
  labels = cur.fetchall()
  labels = get_flat_list(labels)
  return labels

def make_article(items, labels, article):
  for item in article:
    try:
      items.append(item.isoformat())
    except Exception:
      items.append(item)

  article = dict(zip(labels, items))
  return article

def make_index(index, labels, values):
  for article in values:
    # convert type objects to string
    items = []
    article = make_article(items, labels, article)
    index.append(article)
  return index

# + + +

#-- get `article.mod` && `article.url` from `scraper`
def get_mod(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT url FROM scraper WHERE publisher = %s;", (publisher,))
    urls = cur.fetchall()
    urls = get_flat_list(urls)

    # set timezone to UTC `+00` when fetching from db
    # so it matches w/ ciso8601 default settings `+00`
    # http://initd.org/psycopg/docs/usage.html#time-zones-handling
    cur.execute("SET TIME ZONE 'UTC';")

    cur.execute("SELECT DISTINCT mod FROM scraper WHERE publisher = %s;", (publisher,))
    tss = cur.fetchall()
    tss = get_flat_list(tss)
    tss = [ts.isoformat() for ts in tss]

    mod = dict(zip(tss, urls))

    cur.close()
    return mod

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get `article.body` data from `scraper`
def get_body(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- labels
    labels = get_labels(cur, 'scraper')

    #-- values
    cur.execute("SET TIME ZONE 'UTC';")
    cur.execute("SELECT DISTINCT %s FROM scraper WHERE publisher = '%s';" % (', '.join(labels), publisher))
    values = cur.fetchall()

    index = []
    for article in values:

      # convert type objects into string
      art = []
      for item in article:
        try:
          art.append(item.isoformat())
        except Exception:
          art.append(item)

      article = dict(zip(labels, art))
      index.append(article)

    cur.close()
    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get all articles
def get_allarticles():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- labels
    labels = get_labels(cur, 'metadata')

    #-- values
    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata;" % (', '.join(labels),))
    values = cur.fetchall()

    cur.close()

    index = []
    make_index(index, labels, values)
    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get all articles
def get_allarticles_word_freq():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    register_composite('word_freq', cur)

    #-- values
    cur.execute("SET TIME ZONE 'UTC'; SELECT title, publisher, word_freq::word_freq[] FROM tokens;")
    values = cur.fetchall()
    cur.close()

    labels = ['title', 'publisher', 'word_freq']
    index = []

    for article in values:
      # convert type objects to string
      items = []

      for item in article:
        try:
          wf = []
          for value in item:
            cluster = {
              'word': value.word,
              'frequency': str(value.frequency),
              'relativity': str(value.relativity)
            }
            wf.append(cluster)

          items.append(wf)
        except Exception:
          items.append(item)

      article = dict(zip(labels, items))
      index.append(article)

    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get metadata from publisher
def get_pub_articles(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- labels
    labels = get_labels(cur, 'metadata')

    #-- values
    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata WHERE publisher = '%s';" % (', '.join(labels), publisher,))
    values = cur.fetchall()
    cur.close()

    index = []
    make_index(index, labels, values)
    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get pub word_freq
def get_pub_articles_word_freq(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    register_composite('word_freq', cur)

    #-- values
    cur.execute("SET TIME ZONE 'UTC'; SELECT title, publisher, word_freq::word_freq[] FROM tokens WHERE publisher = '%s';" % (publisher,))
    values = cur.fetchall()
    cur.close()

    labels = ['title', 'publisher', 'word_freq']
    index = []

    for article in values:
      # convert type objects to string
      items = []

      for item in article:
        try:
          wf = []
          for value in item:
            cluster = {
              'word': value.word,
              'frequency': str(value.frequency),
              'relativity': str(value.relativity)
            }
            wf.append(cluster)

          items.append(wf)
        except Exception:
          items.append(item)

      article = dict(zip(labels, items))
      index.append(article)

    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get tokens from all pubs except the one passed in the arg
def get_metadata(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- get list of publishers and take out the one passed
    cur.execute("SELECT DISTINCT publisher FROM metadata")
    pubs = cur.fetchall()
    pubs = get_flat_list(pubs)
    pubs.remove(publisher)
    pubs = tuple(pubs)

    #-- labels
    labels = get_labels(cur, 'metadata')

    #-- values
    cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT %s FROM metadata WHERE publisher IN %s;" % (', '.join(labels), pubs))
    values = cur.fetchall()
    cur.close()

    index = []
    make_index(index, labels, values)
    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get random article from publisher
def get_random_article():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- labels
    labels = get_labels(cur, 'metadata')

    #-- values
    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata ORDER BY random() limit 1;" % (', '.join(labels),))
    article = cur.fetchone()
    cur.close()

    items = []
    article = make_article(items, labels, article)
    return article

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get specigic article (id)
def get_specific_article(article_id, labels):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- labels
    if labels is None:
      labels = get_labels(cur, 'metadata')
    else:
      labels = labels

    print(labels)

    #-- values
    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata WHERE id = '%s';" % (', '.join(labels), article_id))
    article = cur.fetchone()
    cur.close()

    items = []
    article = make_article(items, labels, article)
    return article

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get tokens from all pubs except the one passed in the arg
def get_corpus(publisher, **labels):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    # -- get list of publishers and take out the one passed
    cur.execute("SELECT DISTINCT publisher FROM metadata")
    pubs = cur.fetchall()
    pubs = get_flat_list(pubs)
    pubs.remove(publisher)
    pubs = tuple(pubs)

    index = {}
    for pub in pubs:
      cur.execute("SELECT COUNT(*) FROM tokens WHERE publisher = %s", (pub,))
      count = cur.fetchone()[0]
      index[pub] = count

    labels = list(labels.keys())
    labels = ["token_{0}".format(item) for item in labels]

    cur.execute("SELECT %s FROM tokens WHERE publisher IN %s;" % (",".join(labels), pubs))
    tokens = cur.fetchall()
    tokens = get_flat_list(tokens)

    results = {
      'index': index,
      'data': tokens
    }

    cur.close()
    return results

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get tokens from specific article
def get_article_corpus(article_id, *args):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("SELECT %s FROM tokens WHERE id = %s", (",".join(args), article_id))
    tokens = cur.fetchall()
    tokens = get_flat_list(tokens)

    results = tokens

    cur.close()
    return results

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')
