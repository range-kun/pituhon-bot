#!/bin/bash

if [ "$DATABASE" = "postgres" ]
then
  echo "Waiting for postgres..."

  while ! nc -z "$POSTGRES_HOST"  "$POSTGRES_PORT"; do
    sleep 0.1
  done

  echo "PostgresSQL started"
fi

# python3 manage.py flush --no-input
alembic revision --autogenerate
alembic upgrade head

exec "$@"