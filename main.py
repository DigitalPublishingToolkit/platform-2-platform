import sys
import requests
from bs4 import BeautifulSoup
import ac
import oo
import oss
import osr
from text_processing import text_cu, stop_words, unique_words, tags_filter
import nltk
import save_to_db
import get_from_db
from datetime import timezone
import ciso8601
import gensim
from gensim import corpora
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.test.utils import get_tmpfile

import collections
import random
import csv

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

#----
# run scraper with list of urls to check for scraping
# - read urls from db
# - check with db if url has been updated since last time,
#   then run the scrape function on new urls &
#   add them to the db, else do nothing
#   maybe save the timestamp of latest sitemap checkup

#-- shape data up
def text_processing(article):
  tags = tags_filter(article['tags'])
  # print(tags)
  article['tags'] = tags

  corpus = ' '.join([article['title'], ' '.join(tags), article['body']])

  words = text_cu(corpus)
  words = nltk.word_tokenize(words)
  words = stop_words(words, article)
  words = unique_words(words, article)
  article['tokens'] = words

  print('text processing done')
  # print(article)

  return article


#-- main
articles = []

def main(name, articles):
  names = {'ac': 'amateur-cities',
           'oo': 'online-open',
           'os': 'open-set',
           'osr': 'open-set-reader'}

  publisher = names[name]

  if(sys.argv[2] == 'sc'):
    #-- get sitemap
    sitemap = {'ac': 'https://amateurcities.com/post-sitemap.xml',
               'oo': 'https://www.onlineopen.org/sitemap.xml',
               'os': 'http://hub.openset.nl/backend/wp-json',
               'osr': 'http://openset.nl/reader/pocket/api/get.php?type=root&id=root'}

    #-- open-set apis
    apis = {'sections': [{'type': 'project',
                          'url': 'http://hub.openset.nl/backend/wp-json/wp/v2/project',
                          'data': {}},
                         {'type': 'expertinput',
                          'url': 'http://hub.openset.nl/backend/wp-json/swp_api/search',
                          'data': {}}, ],
            'categories': {'type': 'categories',
                           'url': 'http://hub.openset.nl/backend/wp-json/wp/v2/categories',
                           'data': {}}}

    t_url = sitemap[name]
    r = requests.get(t_url)
    data = r.text

    #-- make dict with { <lastmod>: <url> }
    soup = BeautifulSoup(data, "lxml")

    def get_sitemap(data, key, arr):
      for item in data.find_all(key):
        arr.append(item.text)

    url = []
    mod = []
    get_sitemap(soup, 'loc', url)
    get_sitemap(soup, 'lastmod', mod)

    # for online-open (and anyone else), let's force add a UTC timezone
    # at the end of the date-timestamp, so we can match the date-timestamp
    # coming from the postgresql db, which automatically at a UTC tz as well
    # (this means a `+00:00` after `2019-07-04T22:00:00`, therefore
    # all date-timestamp are now in the full isodate format of
    # `2019-07-04T22:00:00+00:00`
    mod = [ciso8601.parse_datetime(mod).astimezone(tz=timezone.utc).isoformat() for mod in mod]
    last_mod = dict(zip(mod, url))

    datb_mod = get_from_db.get_mod(publisher)

    #--- compare mod from db w/ mod from fresh scraping lookup
    # https://blog.softhints.com/python-compare-dictionary-keys-values/

    def scrape_lookup(datb_mod, last_mod, publisher):
      # check if db has records of this publisher
      index_diff = {}
      if bool(datb_mod) is True:
        db_mod = set(datb_mod.keys())
        sc_mod = set(last_mod.keys())
        mod_diff = sc_mod.difference(db_mod)

        # https://stackoverflow.com/a/17665928
        def ts_diff(diff, main_list):
          y = [k for k in main_list if k not in diff]
          return {k: main_list[k] for k in main_list if k not in y}

        # diff b/t fresh scraped articles and db
        index_diff['action'] = 'update'
        index_diff['entries'] = ts_diff(mod_diff, last_mod)
        index_diff['count'] = len(index_diff['entries'])

        print('-- index-diff --')
        print(index_diff)

        return index_diff
      else:
        print('db data for %s is still empty' % publisher)
        index_diff['action'] = 'add'
        index_diff['entries'] = last_mod
        index_diff['count'] = len(index_diff['entries'])
        return index_diff

    # this is the index_diff b/t db articles and online www
    mod_list = scrape_lookup(datb_mod, last_mod, publisher)

    def add_to_db(mod_list_count, mod_list_action, article, old_article):
      # check mod_list['action'] type to pick between
      # `scrape_update` & `scrape`
      if mod_list_count >= 0 and mod_list_action == 'update':
        print('update db record')
        save_to_db.scrape_update(article, old_article)
      else:
        print('save to db')
        save_to_db.scrape(article)

    #--- scraping + saving
    def scrape(name, publisher, mod_list, sitemap):
      with requests.Session() as s:

        # ac
        if (name == 'ac'):
          for mod, url in mod_list['entries'].items():
            old_article = url
            article = {}
            ac.scraper(s, mod, url, publisher, article)
            articles.append(article)

            add_to_db(mod_list['count'], mod_list['action'], article, old_article)

        # oo
        elif (name == 'oo'):
          for mod, url in mod_list['entries'].items():
            old_article = url
            article = {}
            oo.scraper(s, mod, url, publisher, article)
            articles.append(article)

            add_to_db(mod_list['count'], mod_list['action'], article, old_article)

        # ---
        # not using `add_to_db` function for os and osr
        # just checking if articles are saved in db once
        # after that no more scraping;
        # for os no more articles, for osr some new articles
        # will be manually added to db

        # os
        elif (name == 'os'):
          # feed `apis[item.data{}]` w/ data
          def getData(item):
            item['data'] = requests.get(item['url']).json()

          # fetch data for sections items and categories
          for section in apis['sections']:
            getData(section)

          getData(apis['categories'])

          if mod_list['count'] >= 0 and mod_list['action'] == 'add':
            for item in section['data']:
              article = {}
              oss.scraper(section, item, apis, article)
              articles.append(article)
              save_to_db.scrape(article)
          else:
            print('os: db is full, no new articles to fetch')

        # osr
        elif (name == 'osr'):
          # data = requests.get(sitemap['osr']).json()
          # obj = data['_pocketjoins']['map']

          def get_sitemap(path):
            slugs = []
            with open(path) as tsv:
              tsv = csv.reader(tsv, delimiter='\t')
              for row in tsv:
                slugs.append(row[1].split('/')[-1])

            return slugs

          slug_list = get_sitemap('store/open-set-articles.tsv')
          print(slug_list)

          # index = []
          # for item in obj:
          #   for entry in item['_pocketjoins']['map']:
          #     if (entry['publish'] is True):
          #       index.append(entry['_pocketindex'])

          if mod_list['count'] >= 0 and mod_list['action'] == 'add':
            # for slug in index:
            for slug in slug_list:
              article = {}
              osr.scraper(s, slug, article)
              articles.append(article)
              save_to_db.scrape(article)
          else:
            print('osr: db is full, no new articles to fetch')

        else:
          print('mod_list empty: nothing to scrape')

    #-- scrape
    scrape(sys.argv[1], publisher, mod_list, sitemap)

  # 2. process
  elif (sys.argv[2] == 'tx'):
    articles = get_from_db.get_body(publisher)

    for item in articles:
      try:
        article = text_processing(item)
        save_to_db.metadata(article)
        save_to_db.tokens(article)
      except Exception as e:
        print('text-processing ERROR:', e)

  # 3. send suggestions
  elif (sys.argv[2] == 'tv'):
    # -- get article metadata from all pubs except the one passed as `arg`
    metadata = get_from_db.get_metadata(publisher)
    print(metadata)

    # -- get corpuses from all pubs except the one passed as `arg`
    input_corpus = get_from_db.get_corpus(publisher)
    print(input_corpus['index'], len(input_corpus['data']))

    dictionary = corpora.Dictionary(input_corpus['data'])
    # print(dictionary)

    corpus = [dictionary.doc2bow(text) for text in input_corpus['data']]
    # print(corpus)

    documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(input_corpus['data'])]
    # print(documents)

    # setup model
    model = Doc2Vec(dm=1, vector_size=50, window=2, min_count=2, workers=4, epochs=40)
    # model = Doc2Vec(size=100, window=10, min_count=5, workers=11, alpha=0.025, iter=20)

    pubs = ['amateur-cities', 'online-open', 'open-set-reader']
    pubs.remove(publisher)
    pubs = '_'.join(pubs)
    print('PUBS', pubs)

    # save model to disk
    fn_model = get_tmpfile(pubs)
    model.save(fn_model)

    model = Doc2Vec.load(fn_model)
    model.build_vocab(documents)
    model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)

    # check if model is giving good results:
    # check trained docs with themselves,
    # and check percentage of "sameness"
    ranks = []
    second_ranks = []
    for doc_id in range(len(documents)):
      inferred_vector = model.infer_vector(documents[doc_id].words)
      sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))
      rank = [docid for docid, sim in sims].index(doc_id)
      ranks.append(rank)
      second_ranks.append(sims[1])

    print('-- MOST SIMILAR DOC')
    print('Document ({}): «{}»\n'.format(doc_id, ' '.join(documents[doc_id].words)))
    print(u'SIMILAR/DISSIMILAR DOCS PER MODEL %s:\n' % model)
    for label, index in [('MOST', 0), ('SECOND-MOST', 1), ('MEDIAN', len(sims) // 2), ('LEAST', len(sims) - 1)]:
      title = metadata[documents[index].tags[0]]['title']
      url = metadata[documents[index].tags[0]]['url']
      abstract = metadata[documents[index].tags[0]]['abstract']
      print(u'- %s\n- %s\n- %s\n- %s %s: «%s»\n' % (title, url, abstract, label, sims[index], ' '.join(documents[sims[index][0]].words)))

    # # Pick a random document from the corpus and infer a vector from the model
    # doc_id = random.randint(0, len(documents) - 1)

    # # Compare and print the second-most-similar document
    # print('-- SECOND-MOST-SIMILAR DOCUMENT')
    # dtitle = articles[documents[doc_id].tags[0]]['title']
    # durl = articles[documents[doc_id].tags[0]]['url']
    # dabstract = articles[documents[doc_id].tags[0]]['abstract']
    # print('Train Document ({}):\n- {}\n- {}\n- {}\n«{}»\n'.format(doc_id, dtitle, durl, dabstract, ' '.join(documents[doc_id].words)))
    # sim_id = second_ranks[doc_id]
    # stitle = articles[documents[sim_id[0]].tags[0]]['title']
    # surl = articles[documents[sim_id[0]].tags[0]]['url']
    # sabstract = articles[documents[sim_id[0]].tags[0]]['abstract']
    # print('Similar Document {}:\n- {}\n- {}\n- {}\n«{}»\n'.format(sim_id, stitle, surl, sabstract, ' '.join(documents[sim_id[0]].words)))


if __name__ == '__main__':
  main(sys.argv[1], articles)
