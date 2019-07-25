import time
import json

def store (name, articles):
  filename = name

  with open('store/%s.json' % filename, 'w') as fp:
    json.dump(articles, fp)

    print('stored json!')

def dump (name, articles):
  timestamp = time.strftime("%Y-%m-%d-%H%M%S")
  filename = name + '_' + timestamp

  #-- for datetime problem, see https://code-maven.com/serialize-datetime-object-as-json-in-python
  with open('dump/%s.json' % filename, 'w') as fp:
    json.dump(articles, fp)

    print('dumped to json!')
