import psycopg2
from psycopg2.extras import register_composite
from config import config
import json
from collections import Counter, OrderedDict
import save_to_json

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

def get_feedback_articles():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("SET TIME ZONE 'UTC'; SELECT * FROM feedback;")

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

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
      metadata.slug input_slug,
      feedback.match_slug match_slug,
      feedback.match_publisher,
      feedback.score,
      feedback.timestamp
      FROM metadata
      INNER JOIN feedback ON metadata.slug = feedback.input_slug;
      """)

    cross_q = cur.fetchall()
    feedback_q = [list(item) for item in cross_q]

    feedbacks = []
    for match in feedback_q:
      feedback = {'input_slug': match[0],
                  'match_slug': match[1],
                  'match_publisher': match[2],
                  'score': match[3],
                  'timestamp': match[4].isoformat()}
      feedbacks.append(feedback)

    return feedbacks

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

def get_publisher_matched(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    def get_articles_matched(field_slug, field_pub, publisher):
      cur.execute("""
        SET TIME ZONE 'UTC';
        SELECT
        metadata.url,
        feedback.%s,
        feedback.%s
        FROM metadata INNER JOIN feedback
        ON metadata.slug = feedback.%s AND feedback.%s = '%s';
        """ % (field_slug, field_pub, field_slug, field_pub, publisher,))

      return cur.fetchall()

    articles_input = get_articles_matched('input_slug', 'input_publisher', publisher)
    articles_match = get_articles_matched('match_slug', 'match_publisher', publisher)
    articles = articles_input + articles_match
    matched = set(articles)
    print('matched', matched)

    index = []
    for item in matched:
      article = {'url': item[0],
                 'slug': item[1],
                 'publisher': item[2]}

      index.append(article)

    return index

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

    cur.execute("SET TIME ZONE 'UTC'; SELECT slug,url,publisher FROM metadata WHERE publisher = '%s'" % (publisher,))

    values = cur.fetchall()
    articles = []
    make_index(articles, ['slug', 'url', 'publisher'], values)

    articles_matched = get_publisher_matched(publisher)
    print('ARTICLES_MATCHED', articles_matched, len(articles_matched))

    # convert list of dictionaries to set of dictionaries, <https://stackoverflow.com/a/39204359>
    articles_set = set(json.dumps(item, sort_keys=True) for item in articles)
    articles_matched_set = set(json.dumps(item, sort_keys=True) for item in articles_matched)
    print('ARTICLES_MATCHED_SET', articles_matched_set, len(articles_matched_set))

    articles_diff = articles_set.difference(articles_matched_set)
    print('ARTICLES_DIFF', articles_diff)
    # convert set of dictionaries to list of dictionaries by using `json.loads`
    articles_unmatched = list(json.loads(item) for item in articles_diff)

    return articles_unmatched

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

def get_articles_all_matches():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    labels = get_labels(cur, 'feedback')

    cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT * FROM feedback")
    values = cur.fetchall()

    articles = []
    make_index(articles, labels, values)

    print('ALL MATCHES', articles)

    if not articles or articles is None:
      articles = [{'message': 'no matches yet'}]
      return articles
    else:
      return articles

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

def get_feedback_match(input_publisher, input_slug):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("""
      SET TIME ZONE 'UTC';
      SELECT
      metadata.slug input_slug,
      feedback.match_slug,
      feedback.match_publisher,
      feedback.score,
      feedback.timestamp
      FROM metadata
      INNER JOIN feedback ON metadata.slug = feedback.input_slug
      WHERE metadata.publisher = '%s' AND metadata.slug = '%s';
      """ % (input_publisher, input_slug))

    cross_q = cur.fetchall()
    feedback_q = [list(item) for item in cross_q]

    feedbacks = []
    for match in feedback_q:
      feedback = {'input_slug': match[0],
                  'match_slug': match[1],
                  'match_publisher': match[2],
                  'score': match[3],
                  'timestamp': match[4].isoformat()}

      feedbacks.append(feedback)

    return feedbacks

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

def get_match_progress():
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

    index = {}

    # get score average value across all matched articles
    cur.execute("SET TIME ZONE 'UTC'; SELECT AVG(score) FROM feedback;")
    score = cur.fetchone()[0]
    index['score (average)'] = float(score)

    #-- get all tags from across all matched articles
    # fetch all slugs from the matches
    cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT input_slug, match_slug FROM feedback;")
    articles_t = cur.fetchall()
    articles_t = get_flat_list(articles_t)

    # loop over slugs and fetch tags from each article
    tags = Counter()
    for slug in articles_t:
      cur.execute("SET TIME ZONE 'UTC'; SELECT tags FROM metadata WHERE slug = '%s';" % (slug))
      r = cur.fetchall()
      for item in r:
        for t in item[0]:
          tags[t] += 1

    index['tags'] = OrderedDict(tags.most_common())

    def get_pub_slugs(field_slug, field_pub, pub):
      cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT %s FROM feedback WHERE %s = '%s';" % (field_slug, field_pub, pub,))
      articles = cur.fetchall()
      return articles

    #-- get number of pub matching
    def get_pub_to_pub_matching(input_pub, match_pub):
      cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT input_slug FROM feedback WHERE input_publisher = '%s' AND match_publisher = '%s';" % (input_pub, match_pub))
      r_input = cur.fetchall()

      cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT match_slug FROM feedback WHERE input_publisher = '%s' AND match_publisher = '%s';" % (match_pub, input_pub))
      r_match = cur.fetchall()

      articles = r_input + r_match
      results = len(set(articles))
      return results

    pub_index = []
    for publisher in pubs:
      #-- get publisher's total number of articles
      cur.execute("SET TIME ZONE 'UTC'; SELECT COUNT(*) FROM metadata WHERE publisher = '%s';" % (publisher,))
      total = cur.fetchone()[0]

      input_articles = get_pub_slugs('input_slug', 'input_publisher', publisher)
      match_articles = get_pub_slugs('match_slug', 'match_publisher', publisher)

      articles = input_articles + match_articles
      matched = len(set(articles))
      done = matched * 100 / total

      diff = [p for p in pubs if p != publisher]

      pub2pub_match = {}
      for p in diff:
        r = get_pub_to_pub_matching(publisher, p)
        pub2pub_match[p] = r

      # -- make dict
      entry = {'publisher': publisher,
               'total': total,
               'matched': matched,
               'done': done,
               'pub2pub-matching': pub2pub_match}

      pub_index.append(entry)

    index['publishers'] = pub_index

    # which publishers overlapped the most with whom
    # add to index as root item 

    return index

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

    #-- article matching is based on db article id
    #-- `input_id` is not part of `feedback`, but comes
    #-- from `metadata`; check `get_feedback_matches`
    def make_index(index, labels, values):
      for article in values:
        matches = [x for x in feedbacks if x['input_id'] == article[0]]

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

    #-- article matching is based on db article id
    def make_index(index, labels, values):
      for article in values:
        matches = [x for x in feedbacks if x['input_slug'] == article[-1]]

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
    print('get-pub-articles => db error:', error)
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

    # write index to disk as to avoid to let `online-open` to crash the server
    if (publisher == 'online-open'):
      save_to_json.dump('online-open-wf', index)
    else:
      return index

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

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

#-- get metadata for selected publisher
def get_metadata_for_pub(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    labels = get_labels(cur, 'metadata')

    cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT %s FROM metadata WHERE publisher = '%s';" % (', '.join(labels), publisher))
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

def get_metadata_from_hash(publisher, hashes):
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

    cur.execute("SET TIME ZONE 'UTC'; SELECT DISTINCT %s FROM metadata WHERE hash IN %s;" % (', '.join(labels), hashes))
    values = cur.fetchall()

    cur.close()

    # index = []
    # make_index(index, labels, values)

    index = {}
    for article in values:
      items = []
      article = make_article(items, labels, article)
      index[article['hash']] = article

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
    if labels is None or not labels:
      labels = get_labels(cur, 'metadata')
    else:
      labels = labels

    print(labels)

    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata WHERE id = '%s';" % (', '.join(labels), article_id))
    article = cur.fetchone()
    feedbacks = get_feedback_matches()
    cur.close()

    items = []
    article = make_article(items, labels, article)

    #-- article matching is based on db article id
    matches = [x for x in feedbacks if x['input_id'] == article['id']]
    article['matches'] = matches

    return article

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get specific article by publisher (<pub>/<slug>)
def get_article_by_pub_slug(pub, slug, labels):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- labels
    if labels is None or not labels:
      labels = get_labels(cur, 'metadata')
    else:
      labels.append('slug')
      labels = labels

    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata WHERE publisher = '%s' AND slug = '%s';" % (', '.join(labels), pub, slug))
    article = cur.fetchone()
    feedbacks = get_feedback_matches()
    cur.close()

    items = []
    article = make_article(items, labels, article)

    #-- article matching is based on db article['slug']
    matches = [x for x in feedbacks if x['input_slug'] == article['slug']]
    article['matches'] = matches

    return article

  except (Exception, psycopg2.DatabaseError) as error:
    print('get_article_by_pub_slug => db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- get specific article (slug)
def get_article_by_slug(article_slug, labels):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    #-- labels
    if labels is None or not labels:
      labels = get_labels(cur, 'metadata')
    else:
      labels = labels

    print(labels)

    cur.execute("SET TIME ZONE 'UTC'; SELECT %s FROM metadata WHERE slug = '%s';" % (', '.join(labels), article_slug))
    article = cur.fetchone()
    feedbacks = get_feedback_matches()
    cur.close()

    items = []
    article = make_article(items, labels, article)

    #-- article matching is based on db article id
    matches = [x for x in feedbacks if x['input_id'] == article['id']]
    article['matches'] = matches

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

    # transform article fields from /ask POST from `title` => `token_title`
    # to get actual tokens
    labels_body = list(labels.keys())
    labels_body = ["token_{0}".format(item) for item in labels_body]

    # add `hash` field to be able to map later on in `ask.py` what's the article to query from db.metadata
    labels_head = ['hash']
    labels = labels_head + labels_body

    cur.execute("SELECT %s FROM tokens WHERE publisher IN %s;" % (",".join(labels), pubs))
    values = cur.fetchall()
    cur.close()

    tokens = []
    for item in values:
      tks = []
      for i in range(1, 4):
        for unit in item[i]:
          tks.append(unit)

      article = {'hash': item[0],
                 'tokens': tks}
      tokens.append(article)

    results = {'index': index,
               'data': tokens}

    return results

  except (Exception, psycopg2.DatabaseError) as error:
    print('get_corpus => db error:', error)
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

def get_empty_tags(pub):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("""
      SELECT
      metadata.url,
      scraper.tags
      FROM metadata
      LEFT JOIN scraper ON metadata.url = scraper.url
      WHERE metadata.tags = '{}' AND metadata.publisher='%s';
      """ % (pub,))

    values = cur.fetchall()
    cur.close()

    articles = []
    for item in values:
      item = {'url': item[0],
              'tags': item[1]}

      articles.append(item)

    return articles
    
  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')
