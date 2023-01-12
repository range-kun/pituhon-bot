#!/bin/bash

set -o allexport; source .env; set +o allexport

DB_LOCAL="$(echo -e "$DB_LOCAL_NAME" | tr -d '[:space:]')"

if [ "$DB_LOCAL" = "discord_db_container" ]
then
  echo "Waiting for postgres..."

  while ! nc -z -v "$DB_HOST"  "5432"; do
    sleep 0.1
  done

  echo "PostgresSQL started"
fi

# python3 manage.py flush --no-input
alembic upgrade head
echo "OK 3"

exec "$@"