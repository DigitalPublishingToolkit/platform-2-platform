import contractions
from nltk.corpus import stopwords
from nltk import ngrams, FreqDist, pos_tag
import re

#-- text-clean-up
def text_cu(text):
  # take out punctuation
  text = re.sub(r'[^\w\s]', '', text)
  text = text.lower()

  # expand to contraction form
  text = contractions.fix(text)

  return text


#-- stop-words
def stop_words(text, article):
  sw = set(stopwords.words('english'))

  stop_words = []
  wordsclean = []
  for w in text:
    if w in sw:
      stop_words.append(w)
    else:
      wordsclean.append(w)

  return wordsclean


def pos(corpus, article):
  tk = pos_tag(corpus)
  words = []
  # take out adverbs, but why?
  for word, code in tk:
    if (code != 'RB'):
      words.append(word)

  return words


#-- gonna replace both `word-frequency`,
# `n-word phrases frequency` and
# `relevancy` with `word2vec` and `doc2vec`
# using `gensim`

#-- word-frequency
def word_freq(corpus, article):
  wordfreq = []
  wf = FreqDist(corpus)

  for word, freq in wf.most_common():
    # print(word, freq)

    # (word-frequency / body-tokens-length ) * 100
    rel = (freq / len(corpus)) * 100
    wwf = word, freq, rel

    wordfreq.append(wwf)

  article['word-freq'] = wordfreq


#-- n-word phrases frequency
def phrases_freq(text, size, article):
  pf = dict()
  pf = FreqDist(ngrams(text, size))

  article[str(size) + 'w-phrases'] = pf.most_common()


def relevancy(word_freq, article):
  relevancy = 0
  addup = 0
  for word in word_freq:
    addup += word[2]
    relevancy = addup / len(word_freq)

  article['relevancy'] = relevancy
