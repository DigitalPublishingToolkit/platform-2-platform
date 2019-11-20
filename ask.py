import sys
import get_from_db
from gensim import corpora
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import text_processing

def ask(title, publisher, article_id, labels):
    # -- get article metadata from all pubs except the one passed as `arg`
    metadata = get_from_db.get_metadata(publisher)
    # print(metadata)

    # -- get corpuses from all pubs except the one passed as `arg`
    input_corpus = get_from_db.get_corpus(publisher, **labels)
    # print(input_corpus['index'], len(input_corpus['data']))
    # print(input_corpus['data'])

    dictionary = corpora.Dictionary(input_corpus['data'])
    # print(dictionary)

    corpus = [dictionary.doc2bow(text) for text in input_corpus['data']]
    # print(corpus)

    documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(input_corpus['data'])]
    # print(documents)

    pubs = ['amateur-cities', 'online-open', 'open-set-reader']
    pubs.remove(publisher)
    fn_model = '_'.join(pubs)

    # setup model
    def model_setup(documents, fname):
      model = Doc2Vec(documents, dm=1, vector_size=50, window=2, iter=10, min_count=2, workers=4, epochs=40)
      # model.build_vocab(documents)
      print('model initialized', model)

      # save model to disk
      model.save(fname)
      return model

    #-- check if having to build new model again
    # by loading model saved to disk, if it fails
    # build model anew
    try:
      model = Doc2Vec.load(fn_model)
      # model.build_vocab(documents)
    except Exception as e:
      print('model could not be loaded', e)
      model = model_setup(documents, fn_model)

    # NOT
    # model.build_vocab(documents)
    # print
    model_vocab = [word for word in model.wv.vocab]
    # print(model_vocab)

    # -- this return word token and representation of it in vector space
    # my_dict = dict({})
    # for idx, key in enumerate(model.wv.vocab):
    #     my_dict[key] = model.wv[key]
    #     # my_dict[key] = model.wv.get_vector(key)
    #     # my_dict[key] = model.wv.word_vec(key, use_norm=False)
    # print(my_dict)

    def model_training(model, documents):
      model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)
      return model

    try:
      if (sys.argv[3] == 'train'):
        model = model_training(model, documents)
    except Exception as e:
      print('no `train` flag', e)

    article = {}
    #-- convert labels dict to list, pass it to `get_specific_article`
    labels = [k for k, v in labels.items() if v is True]
    words = get_from_db.get_specific_article(article_id, labels)
    print('WORDS')
    print(words)

    if bool(words) is False:
      return {'error': 'article with id %s not found' % article_id}
    else:
      text_processing.vector_tokenize(words, article)

      td = TaggedDocument(article, 1)

      inferred_vector = model.infer_vector(td[0])
      print(inferred_vector)
      #-- we get our most-similar results as documents,
      #-- we set `topn` to return the n of results we want to have
      # sims = model.docvecs.most_similar([inferred_vector], topn=len(documents))
      sims = model.docvecs.most_similar([inferred_vector], topn=100)

      print('SIMS', sims)
      # print('DOC', documents)
      # print('DOC-LEN', len(documents))

      model_vocab = [word for word in model.wv.vocab]
      s_model_tk = set(model_vocab)

      def get_article_vocab(tokens):
        article_tokens = []
        for token in tokens:
          for item in token:
            if type(item) is list:
                article_tokens.append(','.join(item))
            else:
              article_tokens.append(item)

        # print('article_tokens', article_tokens)
        # print('model_vocab', len(model_vocab), 'article_tk', len(article_tokens))

        s_article_tk = set(article_tokens)
        article_vocab = s_article_tk.intersection(s_model_tk)
        # print('article_vocab', article_vocab, len(article_vocab))

        return list(article_vocab)

      #-- convert `article{}` to a list of values by passing
      #-- only keys that are part of the `labels` list,
      #-- which is the list of article fields being requested by Ask
      #-- and based on which to return a list of article matches
      article_tokens = [v for k, v in article.items() if k in labels]

      get_article_vocab(article_tokens)

      results = []
      for index, (tag_id, rate) in enumerate(sims):
        if (rate >= 0.1):
          # print(index, tag_id, rate)
          mod = metadata[documents[index].tags[0]]['mod'],
          url = metadata[documents[index].tags[0]]['url'],
          title = metadata[documents[index].tags[0]]['title']
          publisher = metadata[documents[index].tags[0]]['publisher']
          abstract = metadata[documents[index].tags[0]]['abstract']
          tags = metadata[documents[index].tags[0]]['tags']
          author = metadata[documents[index].tags[0]]['author']
          body = metadata[documents[index].tags[0]]['body']
          images = metadata[documents[index].tags[0]]['images']
          links = metadata[documents[index].tags[0]]['links']
          refs = metadata[documents[index].tags[0]]['refs']
          article_id = metadata[documents[index].tags[0]]['id']
          score = get_from_db.get_feedback_match(article_id)

          article = {
              # 'mod': mod[0],
              # 'url': url[0],
              'title': title,
              'publisher': publisher,
              # 'abstract': abstract,
              # 'tags': tags,
              # 'author': author,
              # 'body': body,
              # 'images': images,
              # 'links': links,
              # 'refs': refs,
              'id': article_id,
              'rate': rate,
              # 'score': score
          }

          token_dict = {}
          tokens = text_processing.process_tokens(article, token_dict)
          tokens = [[v] for k, v in article.items() if k in labels]
          vocab = get_article_vocab(tokens)

          article['vocabulary'] = vocab

        results.append(article)

      return results
