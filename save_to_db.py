import psycopg2
from config import config

#-- utils

#-- from `[('mod',), ...]` to `['mod', ...]`
def get_flat_list(data):
  flat_list = [l[0] for l in data]
  return flat_list

# + + +

#-- save scraped data to `scraper`
def scrape(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO scraper (mod, url, title, publisher, abstract, tags, author, body)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body'])
    )

    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `word_stats`
def word_stats(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO word_stats (body-tokens, body-words-length, relevancy, publisher)
        VALUES (%s, %s, %s, %s);
        """,
        (article['body-tokens'], article['body-words-length'], article['relevancy'], article['publisher'])
    )

    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `word_frequency`
def word_freq(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO word_stats (word, frequency, relative_freq, publisher)
        VALUES (%s, %s, %s, %s);
        """,
        (article['word'], article['frequency'], article['relative_freq'], article['publisher'])
    )

    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `two_word_frequency`
def two_word_freq(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO word_stats (word_01, word_02, frequency, publisher)
        VALUES (%s, %s, %s, %s);
        """,
        (article['word'][0], article['word'][1], article['frequency'], article['publisher'])
    )

    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `three_word_frequency`
def three_word_freq(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO word_stats (word_01, word_02, word_03, frequency, publisher)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (article['word'][0], article['word'][1], article['word'][2], article['frequency'], article['publisher'])
    )

    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `article_body`
def body(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("INSERT INTO article_body (body) VALUES (%s);", (article['body']))

    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

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
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'scraper';")
    labels = cur.fetchall()
    labels = get_flat_list(labels)

    #-- values
    cur.execute("SELECT DISTINCT body FROM scraper WHERE publisher = %s;", (publisher,))
    values = cur.fetchall()
    values = get_flat_list(values)

    body = dict(zip(labels, values))

    cur.close()
    return body

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')


##--- end
