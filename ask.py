from os import path
import get_from_db
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import text_processing

#-- main ref <https://radimrehurek.com/gensim/auto_examples/tutorials/run_doc2vec_lee.html>

def model_setup(documents, fname):
  model = Doc2Vec(vector_size=50, min_count=2, epochs=40)
  print('model initialized', model)
  model.build_vocab(documents)
  print('model vocabulary built')

  # <https://github.com/RaRe-Technologies/gensim/issues/785#issuecomment-234114412>
  # > Unrelated notes about your code: by supplying a corpus to the Doc2Vec constructor, training will automatically occur.
  # model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)
  # print('model is training')

  # save model to disk
  model.save(fname)
  return model

def get_pubs(pub):
  pubs = ['amateur-cities', 'online-open', 'open-set-reader']
  pubs.remove(pub)
  fn_model = '_'.join(pubs)
  return fn_model

def get_article_vocab(tokens, model):
  model_vocab = [word for word in model.wv.vocab]
  s_model_tk = set(model_vocab)

  article_tokens = []
  for token in tokens:
    for item in token:
      if type(item) is list:
          article_tokens.append(','.join(item))
      else:
        article_tokens.append(item)

  s_article_tk = set(article_tokens)
  article_vocab = s_article_tk.intersection(s_model_tk)

  return list(article_vocab)

#--- main func

def ask(slug, publisher, labels):
  # -- get corpuses from all pubs except the one passed as `arg`
  input_corpus = get_from_db.get_corpus(publisher, **labels)

  #-- instead of adding indexical numbers to the tag section of the `TaggedDocument` (it's a tuple: `Taggeddocument(docs, tags)`),
  # let's add the article['hash'] for later cross retrieval when having to make the final list of similar articles by pulling from db.metadata
  documents = [TaggedDocument(doc['tokens'], [doc['hash']]) for i, doc in enumerate(input_corpus['data'])]

  # print(documents)

  #-- get list of pubs except the one passed as `arg` to ask()
  fn_model = get_pubs(publisher)

  #-- check if having to build new model again by loading model saved to disk, if it fails build model anew and train it first
  if path.exists(fn_model):
    model = Doc2Vec.load(fn_model)
  else:
    print('model could not be loaded')
    model = model_setup(documents, fn_model)

  #-- convert labels dict to list, pass it to `get_specific_article`
  article = {}

  # using the below function does not differentiate enough the results for the algorithm, so we don't use it for now (list of articles is small)
  # add only fields that are True sent from the /ask request
  # labels = [k for k, v in labels.items() if v is True]

  labels = [k for k, v in labels.items()]

  # get full article from article publisher and slug passed through /Ask POST
  words = get_from_db.get_article_by_pub_slug(publisher, slug, labels)

  if bool(words) is False:
    return {'error': 'article with slug %s not found' % slug}
  else:
    text_processing.vector_tokenize(words, article)
    vector_l = [item for item in article.values()]

  # <https://stackoverflow.com/a/952952>
  # make flat-list
  vector = []
  for sublist in vector_l:
    for item in sublist:
      vector.append(item)

  # print('VECTOR', vector)
  inferred_vector = model.infer_vector(vector)
  # print('INFERRED_VECTOR', inferred_vector)

  #-- we get our most-similar results as documents, we set `topn` to return the n of results we want to have
  # sims = model.docvecs.most_similar([inferred_vector], topn=len(documents))
  sims = model.docvecs.most_similar([inferred_vector], topn=100)
  # print('SIMS', sims)

  # -- get article metadata from all pubs except the one passed as `arg`
  hashes = tuple([item['hash'] for item in input_corpus['data']])
  metadata = get_from_db.get_metadata_from_hash(publisher, hashes)

  results = []
  #-- iterate over SIMS and use tag_id (`hash`) to pick the corresponding full article from the metadata list of articles
  for index, (tag_id, rate) in enumerate(sims):
    if (rate >= 0.1):
      print('INDEX, TAG_ID, RATE', index, tag_id, rate)
      article = metadata[tag_id]
      # print(article['title'], article['publisher'])

      score = get_from_db.get_feedback_match(publisher, slug)

      # add `rate` and `score` to article from metadata
      article['rate'] = rate
      article['score'] = score

      token_dict = {}
      tokens = text_processing.process_tokens(article, token_dict)
      tokens = [v for k, v in tokens.items() if k in labels]
      vocab = get_article_vocab(tokens, model)

      article['vocabulary'] = vocab

    results.append(article)

  return results
