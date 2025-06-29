#!/bin/bash

# Migrations
python my_detectID/manage.py migrate

# Static Files
python my_detectID/manage.py collectstatic --noinput

# Runserver
python my_detectID/manage.py runserver 0.0.0.0:8000