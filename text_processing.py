from collections import defaultdict
import contractions
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
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

def unique_words(text, article):
  frequency = defaultdict(int)
  for token in text:
    frequency[token] += 1

  tokens = [key for key, value in frequency.items() if value > 1]
  return tokens

def pos(corpus, article):
  tk = pos_tag(corpus)
  words = []
  # take out adverbs, but why?
  for word, code in tk:
    # if (code != 'RB'):
      words.append(word)

  return words

def tags_filter(tags):
  tags_master = ['commons',
                 'labour',
                 'finance and money'
                 'commercialization',
                 'commodification',
                 'capitalism',
                 'archive-memory',
                 'anti-disciplinarity'
                 'learning',
                 'public domain',
                 'image-representation',
                 'architecture',
                 'theory-reflection',
                 'media',
                 'technology',
                 'mobility',
                 'displacement',
                 'movement',
                 'citizenship',
                 'control',
                 'inequity',
                 'colonization',
                 'alternatives',
                 'futures',
                 'activism',
                 'wicked problems',
                 'public space',
                 'conflict',
                 'methods',
                 'ecologies',
                 'care']

  taglist = []
  for tag in tags:
    if tag.lower() in tags_master:
      taglist.append(tag)

  return taglist

def process_metadata(input, article):
  article = {
    "mod": input['mod'],
    "url": input['url'],
    "title": input['title'],
    "publisher": input['publisher'],
    "abstract": input['abstract'],
    "author": input['author']
  }

  tags = tags_filter(input['tags'])
  article['tags'] = tags

  body = re.sub(r'^Share this on\n\n\n\n', '', input['body'])
  body = re.sub(r'\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave$', '', body)
  article['body'] = body

  print('text processing done')
  return article

def process_tokens(input, article):
  tags = tags_filter(input['tags'])
  article['tags'] = tags

  def tokenize(input, flag):
    if flag is True:
      tokens = re.sub(r'^Share this on\n\n\n\n', '', input)
      tokens = re.sub(r'\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave\n\n\n\nSaveSave$', '', tokens)
    tokens = text_cu(input)
    tokens = word_tokenize(tokens)
    tokens = stop_words(tokens, article)
    if flag is True:
      tokens = unique_words(tokens, article)
    return tokens

  article['title'] = tokenize(input['title'], False)
  article['body'] = tokenize(input['body'], True)

  print('text processing done')
  return article

#-- end
