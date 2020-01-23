import psycopg2
from config import config
import json

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
        INSERT INTO scraper (mod, url, title, publisher, abstract, tags, author, body, images, links, refs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body'], article['images'], article['links'], article['refs'])
    )

    conn.commit()
    cur.close()
    print('record saved: %s' % article['url'])

  except (Exception, psycopg2.DatabaseError) as error:
    print('SCRAPER ADD db error:', error)
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
        SET mod = %s, url = %s, title = %s, publisher = %s, abstract = %s, tags = %s, author = %s, body = %s, images = %s, links = %s, refs = %s
        WHERE url = %s;
        """,
        (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body'], article['images'], article['links'], article['refs'], old_art_url)
    )

    conn.commit()
    cur.close()
    print('db record updated: %s' % (article['title']))

  except (Exception, psycopg2.DatabaseError) as error:
    print('SCRAPER UPDATE db error:', error)
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
          SET mod = %s, url = %s, title = %s, publisher = %s, abstract = %s, tags = %s, author = %s, body = %s, images = %s, links = %s, refs = %s, hash = %s, slug = %s
          WHERE title = %s;
          """
      cur.execute(query, (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body'], article['images'], article['links'], article['refs'], article['hash'], article['slug'], article['title']))
      conn.commit()

      print('metadata has been UPDATED for publisher %s' % article['publisher'])

    def metadata_add():
      query = """
          insert into metadata (mod, url, title, publisher, abstract, tags, author, body, images, links, refs, hash, slug)
          values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
          """
      cur.execute(query, (article['mod'], article['url'], article['title'], article['publisher'], article['abstract'], article['tags'], article['author'], article['body'], article['images'], article['links'], article['refs'], article['hash'], article['slug']))
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

    # https://stackoverflow.com/a/11963002
    # insert an array of composite-types is done through
    # `... VALUES(..., %s::word_freq[]);`
    # eg by casting the %s to the composite type *as* an array!

    cur.execute(
        """
        INSERT INTO tokens (title, publisher, token_title, token_author, token_tags, token_body, word_freq, two_word_freq, three_word_freq, hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s::word_freq[], %s, %s, %s);
        """,
        (article['title'], article['publisher'], article['tokens']['title'], article['author'], article['tokens']['tags'], article['tokens']['body'], article['word_freq'], json.dumps(article['2-word_freq']), json.dumps(article['3-word_freq']), article['hash'])
    )

    conn.commit()
    cur.close()

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
        INSERT INTO feedback (input_slug, input_publisher, match_slug, match_publisher, score, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (feedback['input_slug'], feedback['input_publisher'], feedback['match_slug'], feedback['match_publisher'], feedback['score'], feedback['timestamp'])
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
