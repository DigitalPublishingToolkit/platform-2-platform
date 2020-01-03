import get_from_db
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import text_processing

#-- main ref <https://radimrehurek.com/gensim/auto_examples/tutorials/run_doc2vec_lee.html>

def ask(title, publisher, article_id, labels):
    # -- get corpuses from all pubs except the one passed as `arg`
    input_corpus = get_from_db.get_corpus(publisher, **labels)

    #-- instead of adding indexical numbers to the tag section of the `TaggedDocument`,
    # let's add the article['artid'] for later cross retrieval when having to make the final list of similar articles by pulling from db.metadata
    documents = [TaggedDocument(doc['tokens'], [doc['artid']]) for i, doc in enumerate(input_corpus['data'])]
    print('DOCUMENTS', documents)

    # pubs = ['amateur-cities', 'online-open', 'open-set-reader']
    # pubs.remove(publisher)
    # fn_model = '_'.join(pubs)

    model = Doc2Vec(vector_size=50, min_count=2, epochs=40)
    print('model initialized', model)
    model.build_vocab(documents)

    model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)
    print('model is training')

    # -- this return word token and representation of it in vector space
    # my_dict = dict({})
    # for idx, key in enumerate(model.wv.vocab):
    #     my_dict[key] = model.wv[key]
    #     # my_dict[key] = model.wv.get_vector(key)
    #     # my_dict[key] = model.wv.word_vec(key, use_norm=False)
    # print(my_dict)

    #-- convert labels dict to list, pass it to `get_specific_article`
    article = {}

    # add only fields that are True sent from the /ask request
    # labels = [k for k, v in labels.items() if v is True]
    # using the above function does not differentiate enough the results from the algorithm,
    # so we don't use it for now (list of articles is small)
    labels = [k for k, v in labels.items()]

    # get full article from article id passed through /Ask POST
    words = get_from_db.get_specific_article(article_id, labels)

    if bool(words) is False:
      return {'error': 'article with id %s not found' % article_id}
    else:
      text_processing.vector_tokenize(words, article)
      vector_l = [item for item in article.values()]

    # <https://stackoverflow.com/a/952952>
    # flat-list
    vector = []
    for sublist in vector_l:
      for item in sublist:
        vector.append(item)

    # print('VECTOR', vector)
    inferred_vector = model.infer_vector(vector)
    # print('INFERRED_VECTOR', inferred_vector)

    #-- we get our most-similar results as documents, we set `topn` to return
    # the n of results we want to have
    # sims = model.docvecs.most_similar([inferred_vector], topn=len(documents))
    sims = model.docvecs.most_similar([inferred_vector], topn=100)

    print('SIMS', sims)

    # -- get article metadata from all pubs except the one passed as `arg`
    artids = tuple([item['artid'] for item in input_corpus['data']])
    metadata = get_from_db.get_metadata_from_artid(publisher, artids)

    # print('METADATA', metadata)

    results = []
    #-- iterate over SIMS and use tag_id (`artid`) to pick the corresponding
    # full article from the metadata list of articles
    for index, (tag_id, rate) in enumerate(sims):
      if (rate >= 0.1):
        print('INDEX, TAG_ID, RATE', index, tag_id, rate)
        article = metadata[tag_id]

        score = get_from_db.get_feedback_match(article_id)

        # add `rate` and `score` to article from metadata
        article.update({'rate': rate}, {'score': score})

        # token_dict = {}
        # tokens = text_processing.process_tokens(article, token_dict)
        # tokens = [v for k, v in tokens.items() if k in labels]
        # # print('TOKENS FILTERED', tokens)
        # vocab = get_article_vocab(tokens)

        # article['vocabulary'] = vocab

      results.append(article)

    return results
