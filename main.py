import sys
import time

from scraper import scrapple
from text_processing import text_cu, stop_words, word_freq, phrases_freq, relevancy
import nltk
from nltk.stem import WordNetLemmatizer

import io
import csv

#----
# run scraper with list of urls to check for scraping
# - read urls from db
# - check with db if url has been updated since last time,
#   then run the scrape function on new urls &
#   add them to the db, else do nothing
#   maybe save the timestamp of latest sitemap checkup

def main(name):
  #-- scrape article
  articles = scrapple(name)
  print(name, 'articles length →', len(articles))

  #-- shape data up
  def text_processing (article):
    words = text_cu(article['body'])
    words = nltk.word_tokenize(words)

    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words]

    stop_words(words, article)

    word_freq(article['body-tokens'], article)

    phrases_freq(article['body-tokens'], 2, article)
    phrases_freq(article['body-tokens'], 3, article)

    relevancy(article['word-freq'], article)

    print('text processing done...')
    return article

  for article in articles:
    try:
      text_processing(article)
    except:
      print('article has no `body` field')

  #-- save it to db
  def save (article, articles):
    name = names[sys.argv[1]]
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    filename = name + '_' + timestamp

    output = io.StringIO()

    f = csv.writer(open('dump/%s.csv' % filename, 'w'))
    f.writerow(['mod', 'url', 'title', 'publisher', 'abstract', 'tags', 'author', 'section', 'body', 'body-tokens', 'body-words-length', 'word-freq', '2-word phrases', '3-word phrases', 'relevancy'])
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    f.writerow(article.values())

    with open('dump/%s.json' % filename, 'w') as fp:
      json.dump(articles, fp)

    print('saving done...')


if __name__ == '__main__':
  main(sys.argv[1])
