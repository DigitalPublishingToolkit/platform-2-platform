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

#-- save to `article_metadata`
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
          SELECT EXISTS (SELECT 1 FROM article_metadata WHERE title = %s)
          """,
          (article['title'],))

      return cur.fetchone()[0]

    def metadata_update():
      query = """
          UPDATE article_metadata
          SET mod = %s, url = %s, title = %s, publisher = %s, abstract = %s, tags = %s, author = %s
          WHERE title = %s;
          """
      cur.execute(query, (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['title']))
      conn.commit()

      print('article_metadata has been UPDATED for publisher %s' % article['publisher'])

    def metadata_add():
      query = """
          insert into article_metadata (mod, url, title, publisher, abstract, tags, author)
          values (%s, %s, %s, %s, %s, %s, %s);
          """
      cur.execute(query, (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author']))
      conn.commit()

      print('article_metadata has been ADDED for publisher %s' % article['publisher'])

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

    # if table is not empty
    # UPDATE table, else
    # INSERT INTO table

    cur.execute(
        """
        INSERT INTO tokens (title, publisher, tokens)
        VALUES (%s, %s, %s);
        """,
        (article['title'], article['publisher'], article['tokens'])
    )

    conn.commit()
    # cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')

##--- end
