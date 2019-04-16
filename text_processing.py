import contractions
import nltk


from nltk.corpus import stopwords
from nltk import ngrams, FreqDist
import re

#-- text-clean-up
def text_cu (text):
  # take out punctuation
  text = re.sub(r'[^\w\s]', '', text)
  text = text.lower()

  # expand to contraction form
  text = contractions.fix(text)

  return text

#-- stop-words
def stop_words (text, article):
  sw = set(stopwords.words('english'))

  stop_words = []
  wordsclean = []
  for w in text:
    if w in sw:
      stop_words.append(w)
    else:
      wordsclean.append(w)

  article['body-tokens'] = wordsclean
  article['body-words-length'] = len(wordsclean)
  # article['stop-words'] = stop_words

#-- word-frequency
def word_freq (text, article):
  wordfreq = []
  wf = FreqDist(text)
  for word, freq in wf.most_common():
    # (word-frequency / body-tokens-length ) * 100
    rel = (freq / len(article['body-tokens'])) * 100
    wwf = word, freq, rel
    wordfreq.append(wwf)

  article['word-freq'] = wordfreq

#-- n-word phrases frequency
def phrases_freq (text, size, article):
  pf = dict()
  pf = FreqDist(ngrams(text, size))

  article[str(size) + 'w-phrases'] = pf.most_common()

def relevancy (word_freq, article):
  relevancy = 0
  addup = 0
  for word in word_freq:
    addup += word[2]
    relevancy = addup / len(word_freq)

  article['relevancy'] = relevancy
