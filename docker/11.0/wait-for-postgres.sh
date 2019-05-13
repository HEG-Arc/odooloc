#!/bin/bash
# wait-for-postgres.sh

set -e

host="db"

until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$POSTGRES_USER" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 2
done

>&2 echo "Postgres ready - resume startup"


./entrypoint.sh "$@"
