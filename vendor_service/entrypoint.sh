#!/bin/bash
set -e

python manage.py migrate

python manage.py run_grpc_server --port=50051 &
GRPC_PID=$!

python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

trap 'kill $GRPC_PID $DJANGO_PID; exit' SIGINT SIGTERM

wait $DJANGO_PID