platform 2 platform
===================

This project is part of Institute of Network Cultures' [Making Public](http://networkcultures.org/makingpublic/) project.

We're building an article suggestion system, by indexing in a common database the articles of the three online journals taking part in the project. We're doing this by mixing algorithmic suggestions combined with human editorial choice.

Whenever you're reading an article from Journal 1, you'll get suggestions (in the form of online ads) from Journal 2 and 3. Suggestions are based on article topic, title, author, keywoards and text analysis.

We're re-creating a web-ring on a bigger-scale.

## Diagram

1. python scraper(s)
2. python text processing
3. data saved to postgresql database
4. javascript script embedded in each journal website, to talk between journal and database

## Usage

Set python local environment

    $ pyenv local 3.7.3

Enable python virtual environment and run shell

    $ pipenv shell
    
Whenever you need to install a new python module, do

    $ pipenv install <package-name>
    
It will be saved into `Pipfile` and `Pipfile.lock`. You can then do `pipenv install` to install from the `Pipfile`. This is similar to how `npm` and `package.json` work.

## Scraper

To fetch articles from one of the three websites, eg Amateur Cities, do:

    $ python main.py ac sc

the `sc` flag stands for *scrape*. there is another flag so far, `tx` to do text-processing.

- scrape, `sc`
  - Amateur Cities, `ac`
  - Online Open!, `oo`
  - Open Set, `os`
  - Open Set Reader, `osr`
- text-processing `tx`
