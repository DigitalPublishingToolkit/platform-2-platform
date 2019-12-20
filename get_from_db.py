import psycopg2
from psycopg2.extras import register_composite
from config import config
import json

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

def get_feedback_matches():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("""
      SET TIME ZONE 'UTC';
      SELECT
      metadata.id input_id,
      metadata.title,
      feedback.id match_id,
      feedback.input_title,
      feedback.match_title,
      feedback.match_publisher,
      feedback.score,
      feedback.timestamp
      FROM metadata
      INNER JOIN feedback ON metadata.title = feedback.input_title;
      """)

    cross_q = cur.fetchall()
    feedback_q = [list(item) for item in cross_q]

    feedbacks = []
    for match in feedback_q:
      feedback = {'input_id': match[0],
                  'match_title': match[4],
                  'match_publisher': match[5],
                  'score': match[6],
                  'timestamp': match[7].isoformat()}

      feedbacks.append(feedback)

    return feedbacks

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

def get_publisher_unmatched(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("SET TIME ZONE 'UTC'; SELECT title,url,publisher FROM metadata WHERE publisher = '%s'" % (publisher,))

    values = cur.fetchall()
    articles = []
    make_index(articles, ['title', 'url', 'publisher'], values)

    articles_matched = get_publisher_matched(publisher)

    # convert list of dictionaries to set of dictionaries, <https://stackoverflow.com/a/39204359>
    articles_set = set(json.dumps(item, sort_keys=True) for item in articles)
    articles_matched_set = set(json.dumps(item, sort_keys=True) for item in articles_matched)

    articles_diff = articles_set.difference(articles_matched_set)
    # convert set of dictionaries to list of dictionaries by using `json.loads`
    articles_unmatched = list(json.loads(item) for item in articles_diff)

    return articles_unmatched

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

def get_feedback_match(input_id):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("""
      SET TIME ZONE 'UTC';
      SELECT
      metadata.id input_id,
      metadata.title,
      feedback.id match_id,
      feedback.input_title,
      feedback.match_title,
      feedback.match_publisher,
      feedback.score,
      feedback.timestamp
      FROM metadata
      INNER JOIN feedback ON metadata.title = feedback.input_title
      WHERE metadata.id = %s;
      """ % (input_id,))

    cross_q = cur.fetchall()
    feedback_q = [list(item) for item in cross_q]

    feedbacks = []
    for match in feedback_q:
      feedback = {'input_id': match[0],
                  'match_title': match[4],
                  'match_publisher': match[5],
                  'score': match[6],
                  'timestamp': match[7].isoformat()}

      feedbacks.append(feedback)

    return feedbacks

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

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

    labels = get_labels(cur, 'metadata')

    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata;" % (', '.join(labels),))
    values = cur.fetchall()
    feedbacks = get_feedback_matches()
    cur.close()

    def make_index(index, labels, values):
      for article in values:
        matches = [x for x in feedbacks if x['input_id'] == article[7]]

        article = list(article)
        article.append(matches)

        items = []
        article = make_article(items, labels, article)
        index.append(article)
      return index

    index = []
    labels.append('matches')

    make_index(index, labels, values)
    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get all word-frequency
def get_allarticles_word_freq():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    register_composite('word_freq', cur)

    #-- values
    cur.execute("""
      SET TIME ZONE 'UTC';
      SELECT
      tokens.title,
      tokens.publisher,
      tokens.word_freq::word_freq[],
      tokens.two_word_freq,
      tokens.three_word_freq,
      metadata.tags,
      metadata.mod
      FROM tokens INNER JOIN metadata ON tokens.title = metadata.title;
      """)
    values = cur.fetchall()
    cur.close()

    index = []
    for article in values:
      # word_freq
      wf = []
      for value in article[2]:
        cluster = {'word': value.word,
                   'frequency': str(value.frequency),
                   'relativity': str(value.relativity)}
        wf.append(cluster)

      article = {'title': article[0],
                 'publisher': article[1],
                 'mod': article[6].isoformat(),
                 'tags': article[5],
                 'word_freq': wf,
                 '2-word_freq': article[3],
                 '3-word_freq': article[4]}

      index.append(article)

    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get articles from publisher
def get_pub_articles(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    labels = get_labels(cur, 'metadata')

    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata WHERE publisher = '%s';" % (', '.join(labels), publisher,))
    values = cur.fetchall()

    feedbacks = get_feedback_matches()
    cur.close()

    def make_index(index, labels, values):
      for article in values:
        matches = [x for x in feedbacks if x['input_id'] == article[7]]

        article = list(article)
        article.append(matches)

        items = []
        article = make_article(items, labels, article)
        index.append(article)
      return index

    index = []
    labels.append('matches')

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

    cur.execute("""
        SET TIME ZONE 'UTC';
        SELECT
        tokens.title,
        tokens.publisher,
        tokens.word_freq::word_freq[],
        tokens.two_word_freq,
        tokens.three_word_freq,
        metadata.tags,
        metadata.mod
        FROM tokens INNER JOIN metadata ON tokens.title = metadata.title
        WHERE tokens.publisher = '%s';
        """ % (publisher,))
    values = cur.fetchall()
    cur.close()

    index = []

    for article in values:
      # word_freq
      wf = []
      for value in article[2]:
        cluster = {'word': value.word,
                   'frequency': str(value.frequency),
                   'relativity': str(value.relativity)}
        wf.append(cluster)

      article = {'title': article[0],
                 'publisher': article[1],
                 'mod': article[6].isoformat(),
                 'tags': article[5],
                 'word_freq': wf,
                 '2-word_freq': article[3],
                 '3-word_freq': article[4]}

      index.append(article)

    return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get metadata from each publisher
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

    labels = get_labels(cur, 'metadata')

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

    labels = get_labels(cur, 'metadata')

    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata ORDER BY random() limit 1;" % (', '.join(labels),))
    article = cur.fetchone()

    # get list position of `id` from the get_labels() list
    # this avoids problems when making a table with diff field orders
    # eg between local and production tables
    id_pos = [i for i, x in enumerate(labels) if x == 'id'][0]

    feedbacks = get_feedback_match(article[id_pos])
    cur.close()

    labels.append('matches')
    article = list(article)
    article.append(feedbacks)

    items = []
    article = make_article(items, labels, article)
    return article

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get specific article (id)
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
    cur.execute("SELECT DISTINCT publisher FROM metadata;")
    pubs = cur.fetchall()
    pubs = get_flat_list(pubs)
    pubs.remove(publisher)
    pubs = tuple(pubs)

    index = {}
    for pub in pubs:
      cur.execute("SELECT COUNT(*) FROM tokens WHERE publisher = %s;", (pub,))
      count = cur.fetchone()[0]
      index[pub] = count

    labels = list(labels.keys())
    labels = ["token_{0}".format(item) for item in labels]

    cur.execute("SELECT %s FROM tokens WHERE publisher IN %s;" % (",".join(labels), pubs))
    tokens = cur.fetchall()
    tokens = get_flat_list(tokens)

    results = {'index': index,
               'data': tokens}

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
