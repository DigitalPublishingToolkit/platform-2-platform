import psycopg2
from psycopg2 import sql
from config import config

#-- save scraped data to db
def scrape (article):
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


def word_stats (article):
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


def word_freq (article):
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


def two_word_freq (article):
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


def three_word_freq (article):
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


#-- get data back (`body` from current publisher)
def get_body(publisher):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT body FROM scraper WHERE publisher = %s;", (publisher,))
    body = cur.fetchall()

    cur.close()
    return body

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')
