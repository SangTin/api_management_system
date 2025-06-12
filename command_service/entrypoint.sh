#!/bin/bash
set -e

python manage.py migrate

python manage.py start_command_agents --test_agents=1 --device_agents=2 &
AGENTS_PID=$!

python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

trap 'kill $AGENTS_PID $DJANGO_PID; exit' SIGINT SIGTERM

wait $DJANGO_PID