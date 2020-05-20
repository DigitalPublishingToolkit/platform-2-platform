#!/bin/bash
# get path by doing `which gunicorn`
/Users/af-etc/.local/share/virtualenvs/prototype-FN3Htjsq/bin/gunicorn -c gunicorn.conf.py server:app
