import psycopg2
from config import config

# + + +

#-- save scraped data to `scraper`
def scrape(article):
  print('scrape')

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
    print('record saved: %s' % article['url'])

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- update scraped data in `scraper`
def scrape_update(article, old_art_url):
  print('scrape update')

  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE scraper
        SET mod = %s, url = %s, title = %s, publisher = %s, abstract = %s, tags = %s, author = %s, body = %s
        WHERE url = %s;
        """,
        (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body'], old_art_url)
    )

    conn.commit()
    cur.close()
    print('db record updated: %s' % (article['title']))

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `metadata`
def metadata(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    def query_exists():
      cur.execute(
          """
          SELECT EXISTS (SELECT 1 FROM metadata WHERE title = %s)
          """,
          (article['title'],))

      return cur.fetchone()[0]

    def metadata_update():
      query = """
          UPDATE metadata
          SET mod = %s, url = %s, title = %s, publisher = %s, abstract = %s, tags = %s, author = %s, body = %s
          WHERE title = %s;
          """
      cur.execute(query, (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body'], article['title']))
      conn.commit()

      print('metadata has been UPDATED for publisher %s' % article['publisher'])

    def metadata_add():
      query = """
          insert into metadata (mod, url, title, publisher, abstract, tags, author, body)
          values (%s, %s, %s, %s, %s, %s, %s, %s);
          """
      cur.execute(query, (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body']))
      conn.commit()

      print('metadata has been ADDED for publisher %s' % article['publisher'])

    if query_exists() is True:
      print(query_exists())
      metadata_update()
    else:
      print(query_exists())
      metadata_add()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `tokens`
def tokens(article):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO tokens (title, publisher, token_title, token_author, token_tags, token_body)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (article['title'], article['publisher'], article['tokens']['title'], article['author'].lower(), article['tokens']['tags'], article['tokens']['body'])
    )

    conn.commit()
    # cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

#-- save to `feedback`
def feedback(feedback):
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO feedback (input_title, input_publisher, match_title, match_publisher, score, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (feedback['input_title'], feedback['input_publisher'], feedback['match_title'], feedback['match_publisher'], feedback['score'], feedback['timestamp'])
    )

    conn.commit()
    cur.close()

    return {'result': 'feedback saved successfully'}

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

##--- end
