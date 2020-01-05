platform 2 platform

This project is part of Institute of Network Cultures' [Making Public](http://networkcultures.org/makingpublic/) project.

We're building an article suggestion system, by indexing in a common database the articles of the three online journals taking part in the project. We're doing this by mixing algorithmic suggestions combined with human editorial choice.

Whenever you're reading an article from Journal 1, you'll get suggestions (in the form of online ads) from Journal 2 and 3. Suggestions are based on article topic, title, author, tags and text analysis.

We're sort of creating a web-ring powered by machine learning.

## Diagram

1. python scraper(s)
2. python text processing
3. data saved to postgresql database
4. javascript script embedded in each journal website, to talk between journal and database

## Setup

### Intro

First, obligatory disclosure:

We’re using [pyenv](https://github.com/pyenv/pyenv) and [pipenv](https://github.com/pypa/pipenv) to manage the insanely complicated process of running a specific version of python without messing every other python version installed in your system, as well as for managing python packages and therefore dealing with virtual environments.

There are other ways to do this, feel free to use your preferred method. For example using `venv` to manage python virtual environment (we do that with `pipenv shell`) and simply using `pip` and `pip freeze > requirements.txt` for tracking package versions.

To keep following this guide, either install `pyenv` and `pipenv` or swap these two commands with your own appropriate version.

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
- if you try connecting to postgres with `psql postgres` it will say `<user>` has no *role* in postgres yet
- therefore connect to it with the default `postgres` user, by doing `sudo -u postgres -i`
- then do `psql postgres` to enter postgres
- `\du;` to see the list of users
- create a new user `CREATE ROLE <user> WITH LOGIN PASSWORD '<password>';` (tip: use the same username as an existing unix user present in your machine; this will let you to access the PostgreSQL database shell without having to specify a user to login)
- make them create databases by changing their role attributes `ALTER ROLE <user> CREATEDB;`
- log out from psql with `\q` (switching to your default user and trying to connect results in a login error)
- before connecting as a non-super user, create a db for your user, by simply doing `createdb <username>`; this will create a database for psql with the name of your username, psql needs this
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

and then copy pasting each `CREATE TABLE` command listed below and press enter (multiline pasting did work in my tests on different terminals)

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
  artid text
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
  artid text
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
  timestamp timestamptz
);
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
- `os` Open Set (not used, but good for reference) 

### Workfow

A general workflow would consist in:

- scraping a publisher website through their sitemap
- text-processing the scraped data
- tokenize the text-processed data

After these three operations have been done for each publisher, the program can be run. Eg, the article matching algorithm can be utilised by either using the frontend web application, or by sending a `POST` request in the form of:

``` shell
curl -H "content-type: application/json" -d '{ "article_title": "The New Euro-Citizen", "article_publisher": "online-open", "article_id": 839, "tokens": { "title": true, "author": true, "tags": true, "body": true } }' http://127.0.0.1:5000/api/ask
```

To break the `curl` command down:

- `-H "content-type: application/json"`, send a JSON Header
- `-d '{
    "article_title": "The New Euro-Citizen", 
    "article_publisher": "online-open", 
    "article_id": 839, 
    "tokens": {
      "title": true,
      "author": true,
      "tags": true,
      "body": true
      } 
  }'` with a data object containing `article_title`, `article_id` and `tokens` type; the data for these three fields can be retrieved from the text-processed data saved in the database, as well as when running the server from the JSON Rest API, by browsing to a publisher page and pick an article from the (eg `http://127.0.0.1:5000/api/articles/amateur-cities`).

This call will return an array list of articles, containing all the matches found by the suggestion algorithm.

## Known bugs and limitations

### Bugs

When running this program on a debian server environment, `Doc2Vec` reported the following problems when using the suggestion algorithm:

```
AttributeError: 'Doc2Vec' object has no attribute 'syn0' when call infer_vector

Doc2Vec.infer_vector: AttributeError: 'Doc2Vec' object has no attribute 'syn1'
```

Both have been reported already as issues to the gensim github page [#1](https://github.com/RaRe-Technologies/gensim/issues/785) and [#2]((https://github.com/RaRe-Technologies/gensim/issues/483)). It turned out that there seems to be some problem when `Doc2Vec` needs to generate for the first time the model for each new publisher. Somehow it cannot do it and something goes wrong. By copying over the generated models from our macOS environment, the program could work fine.

This is something to fix before moving this program into a reproducible environment (eg Docker or NixOS).

### Limitations

Currently we disabled the option to selectively choose which article fields to use when feeding the algorithm for suggesting new articles. Eg, which content is being used as input data to produce matches. 

This is because results did not change at all, and our impression so far is that it’s because our dataset is very small (~ 600 articles) and Doc2Vec was built to work with thousands of articles (eg average of 50-70 thousands). We’re still working on this and tweaking options in order to see if result would change. Nonetheless, we keep it this option part of the code (both here and in the frontend app) as it would a very interesting element to play with for the publishers during their editorial review matching-process.
