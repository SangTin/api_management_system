#!/bin/bash
set -e

# Chạy migrations
python manage.py migrate

# Chạy server
python manage.py runserver 0.0.0.0:8000