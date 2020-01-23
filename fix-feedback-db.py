import sys
import psycopg2
from config import config
from slugify import slugify

# + + +

def main():
  conn = None
  try:
    params = config()
    print('connecting to db...')
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    cur.execute("SELECT input_title, match_title FROM feedback WHERE input_slug is null;")
    values = cur.fetchall()
    #-- values = (<input_title>, <match_title>)
    print(values)

    conn.commit()

    for entry in values:
      print(entry)
      cur.execute(
          """
          UPDATE feedback
          SET input_slug = %s, match_slug = %s
          WHERE input_title = %s;
          """,
          (slugify(entry[0]), slugify(entry[1]), entry[0])
      )

      conn.commit()
      print(entry[0], 'has been updated')

    cur.close()

    print('operation done successfully')
  except (Exception, psycopg2.DatabaseError) as error:
    print('db error:', error)
  finally:
    if conn is not None:
      conn.close()
      print('db connection closed')


#-- run
main()
