platform 2 platform
===================

*A recommendation tool for networks of independent publishers.*

Platform 2 Platform is a tool that combines an algorithmic matching system and human editorial expertise to create relevant recommendations for further reading across a network of independent publishers. This file contains the technical ReadMe for the tool. To learn more about the concept of the tool and its context, please read about [the political urgency](https://networkcultures.org/makingpublic/2020/03/02/clickbait-revisited/), [its governance and scalability](https://networkcultures.org/makingpublic/2020/02/06/governance-and-scalability-circles-of-trust-and-federated-platforms/), [the origin of the idea](https://networkcultures.org/makingpublic/2018/11/30/platform-2-platform/), and [the potential of relationality in independent publishing](https://networkcultures.org/makingpublic/2020/02/19/making-relationships-public/) on the blog of the project.

## Credits

This tool was developed as part of the [Making Public!](https://networkcultures.org/makingpublic/) research project funded by [SIA RAAK](http://www.regieorgaan-sia.nl/onderzoeksfinanciering/RAAK-mkb). The tool is the product of a collaboration between [André Fincato](https://andrefincato.info/) ([Hackers & Designers](https://hackersanddesigners.nl/)), Niels Schrader and Martijn de Heer ([Mind Design](http://www.minddesign.info/)), Ania Molenda and Cristina Ampatzidou ([Amateur Cities](https://amateurcities.com/)), Jorinde Seijdel ([Open!](https://onlineopen.org/index.php)), Irina Shapiro ([Open Set](http://www.openset.nl/)), [Silvio Lorusso](https://silviolorusso.com/) ([WdKA](https://www.wdka.nl/)) and Inte Gloerich ([Institute of Network Cultures](https://networkcultures.org/), [AUAS](https://www.hva.nl/)).

## Diagram

1. python scraper(s)
2. python text processing and tokenization
3. data saved to postgresql database
4. request article matches through `/api/ask`
5. javascript script embedded in each journal website, to talk between journal and database

## Setup

### Intro

First, obligatory disclosure:

We’re using [pyenv](https://github.com/pyenv/pyenv) and [pipenv](https://github.com/pypa/pipenv) to manage the insanely complicated process of running a specific version of python without messing every other python version installed in the system, as well as for managing python packages and therefore dealing with virtual environments.

There are other ways to do this, feel free to use your preferred method. For example using `venv` to manage python virtual environment (we do that with `pipenv shell`) and simply using `pip` and `pip freeze > requirements.txt` for tracking package versions.

To keep following this guide, either install `pyenv` and `pipenv` or swap these two commands with your own preferred version.

### Python environment

Set python local environment

``` shell
$ pyenv local 3.7.3
```

Enable python virtual environment by starting a shell

``` shell
$ pipenv shell
```
    
Now let’s install all modules listed in the `Pipfile`

``` shell
$ pipenv install
```
    
Then, let’s download the [NLTK dataset](https://www.nltk.org/data.html):

``` shell
$ python -m nltk.downloader all
```

Lastly, important note:

When installing `gensim` (which contains the `Doc2Vec` matching algorithm), if you are not using `pipenv` and installing it manually, make sure to first install `NumPy` and `Scipy`. After that, if you’re on macOS, `NumPy` automatically installs a BLAS (Basic Linear Algebra Subprograms). If you’re on another unix system, install either [ATLAS](http://math-atlas.sourceforge.net/) or [OpenBLAS](https://github.com/xianyi/OpenBLAS/wiki/Precompiled-installation-packages.). This BLAS program will speed up gensim computation a lot!

### Database

We’re using PostgreSQL for the database. Make sure to have `psql` installed and running, to have made a new user (non-superuser), and a table name after your non-superuser user.

Check this as general [reference guide](https://www.codementor.io/@engineerapart/getting-started-with-postgresql-on-mac-osx-are8jcopb). These are personal notes after `psql` has been installed:

- check it is running with `sudo service postgresql status`
- for now postgresql has created a `postgres` user,
- if you try to connect to postgres with `psql postgres`, it will say `<user>` has no *role* in postgres yet
- therefore connect to it with the default `postgres` user, by doing `sudo -u postgres -i`
- then do `psql postgres` to enter postgres
- `\du;` to see the list of users
- create a new user `CREATE ROLE <user> WITH LOGIN PASSWORD '<password>';` (tip: use the same username as an existing unix user present in your machine; this will let you access the PostgreSQL database shell without having to specify a user to login)
- allow this user to create databases by changing their role attributes `ALTER ROLE <user> CREATEDB;`
- log out from psql with `\q` (switching to your default user and trying to connect results in a login error)
- before connecting as a non-super user, create a db for your user, by simply doing `createdb -E utf8 <username>`; this will create a database for psql with the name of your username, psql needs this
- connect to psql again with your new user, by doing `psql -U <user> -h localhost`, type the password when asked; you should be in now!
- create a new db with the logged in user (which is not root / superuser), `CREATE DATABASE <db-name>;`
- grant access to your user `GRANT ALL PRIVILEGES ON DATABASE <db-name> TO <user>;`
- check databases `\list`
- connect to it `\connect <db-name>`
- list tables (should be empty) `\dt`

After this, make the below tables by entering `psql` with:

```
$ psql -U <username> <db-name>
```

and then copy paste each `CREATE TABLE` command listed below and press enter (multiline pasting did work in my tests on different terminals)

#### scraper

```
CREATE TABLE scraper (
  id serial primary key,
  mod timestamptz NOT NULL,
  url text NOT NULL,
  title text NOT NULL,
  publisher text NOT NULL,
  abstract text NOT NULL,
  tags text[] NOT NULL,
  author text[] NOT NULL,
  body text NOT NULL,
  images text[] NOT NULL,
  links text[] NOT NULL,
  refs text[] NOT NULL
);
```

#### metadata

```
CREATE TABLE metadata (
  id serial primary key,
  mod timestamptz NOT NULL,
  url text NOT NULL,
  title text NOT NULL,
  publisher text NOT NULL,
  abstract text NOT NULL,
  tags text[] NOT NULL,
  author text[],
  body text NOT NULL,
  images text[],
  links text[],
  refs text[],
  hash text,
  slug text
);
```

#### tokens

first create a new `TYPE`:

```
CREATE TYPE word_freq AS (
  word text,
  frequency smallint,
  relativity smallint 
);
```

then

```
CREATE TABLE tokens (
  id serial primary key,
  title text NOT NULL,
  publisher text NOT NULL,
  token_title text[],
  token_author text[],
  token_tags text[],
  token_body text[],
  word_freq word_freq[],
  three_word_freq json,
  two_word_freq json,
  hash text
);
```

#### feedback

```
CREATE TABLE feedback (
  id serial primary key,
  input_title text NOT NULL,
  input_publisher text NOT NULL,
  match_title text NOT NULL,
  match_publisher text NOT NULL,
  score smallint NOT NULL,
  timestamp timestamptz,
  input_slug text NOT NULL,
  match_slug text NOT NULL
);
```

finally, create `./db.ini` with the following info:

```
[postgresql]
host=localhost
database=<db-name>
user=<db-user>
password=<db-user-password>
```

## General usage
    
In order to have the program running, we need to do three things:

1. scrape all articles from the three publishers
2. process the raw text into usable data
3. run a server and send `POST` request to it (or use the [frontend app](https://github.com/aptoptout/ionc-making-it-visible))

To fetch articles from one of the three websites, eg Amateur Cities, make sure to be inside a python environment shell (eg, by doing `pipenv shell`), then do:

``` shell
$ python main.py ac sc
```

The `sc` flag stands for *scrape*, while `ac` stands for `Amateur Cities`. These are all the flags:

### List of commands

Actions
- `sc` scrape
- `tx` text-processing
- `tk` text-tokenization

Subject
- `ac` Amateur Cities, 
- `oo` Online Open!, 
- `osr` Open Set Reader, 
- `os` Open Set (not used anymore, but good for reference) 

### Workfow

A general workflow would consist in:

- scraping a publisher website through their sitemap
- text-processing the scraped data
- tokenize the text-processed data

After these three operations have been done for each publisher, the program can be run. Eg, the article matching algorithm can be utilised by either using the frontend web application, or by sending a `POST` request in the form of:

``` shell
curl -H "content-type: application/json" -d '{ "article_slug": "the-new-euro-citizen", "article_publisher": "online-open", "tokens": { "title": true, "author": true, "tags": true, "body": true }, "size": 100 }' http://127.0.0.1:5000/api/ask
```

To break the `curl` command down:

- `-H "content-type: application/json"`, send a JSON Header
- `-d '{
    "article_slug": "the-new-euro-citizen", 
    "article_publisher": "online-open", 
    "article_id": 839,
    "tokens": {
      "title": true,
      "author": true,
      "tags": true,
      "body": true
      },
    "size": 100
  }'` with a data object containing `article_slug`, `article_publisher` and `tokens` type; the data for these three fields can be retrieved from the text-processed data saved in the database, as well as when running the server from the JSON Rest API, by browsing to a publisher page and pick an article from the (eg `http://127.0.0.1:5000/api/articles/amateur-cities`).

This call will return an array list of articles, containing all the matches found by the suggestion algorithm.

## Javascript embedded plugin

As of `<2020-03-14>`, we mocked up the javascript plugin to embed in each publisher’s website.

This script allows to send the current article on view to the article recommendation algorithm, and send back a list of x articles to display on the article webpage. The list of suggested articles are dinamically inserted into the webpage at the bottom of each article’s text.

So far, we have a working sketched out prototype, and aim to turn that into a packaged script that each of the publishers can simply embed to their website by adding a link to the script.

Due to the nature of each publisher having different article DOM structures, the script takes this into account for a few operations. Ideally, this could be avoided by generalizing the plugin code and ask each publishers’ website to add a few extra lines of code around the plugin, so to provide the correct arguments to the main plugin function.

The prototype version of this code can be found here <https://github.com/afincato/mhp-fem>.


## Known bugs and limitations

### Bugs

When running this program on a debian server environment, `Doc2Vec` reported the following problems when using the suggestion algorithm:

```
AttributeError: 'Doc2Vec' object has no attribute 'syn0'

AttributeError: 'Doc2Vec' object has no attribute 'syn1'
```

Both have been reported already as issues to the gensim github page ([#1](https://github.com/RaRe-Technologies/gensim/issues/785) and [#2](https://github.com/RaRe-Technologies/gensim/issues/483)). It turned out that there seems to be some problem when `Doc2Vec` needs to generate for the first time the model for each new publisher. Somehow it cannot do it and something goes wrong. By copying over the generated models from our macOS environment, the program could work fine.

This is something to fix before moving this program into a reproducible environment (eg Docker or NixOS).

### Limitations

Currently we disabled the option to selectively choose which article fields to use when feeding the algorithm for suggesting new articles. Eg, which content is being used as input data to produce matches. 

This is because results did not change at all, and our impression so far is that it’s because our dataset is very small (~ 600 articles) and `Doc2Vec` was built to work with thousands of articles (eg average of 50-70 thousands). We’re still working on this and tweaking options in order to see if result would change. Nonetheless, we keep this option part of the code (both here and in the frontend app) as it would be a very interesting element to play with for the publishers during their editorial review matching-process.
