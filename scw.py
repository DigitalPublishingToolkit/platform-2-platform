import sys
import os
import shutils
import requests

def scrape(url):
  page = requests.get(url)
  print(page.text)

  with open('dump/index.html', 'w') as fp:
    fp.write(page.text)

scrape(sys.argv[1])
