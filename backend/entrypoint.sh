#!/bin/sh
set -e

# Ждём, пока поднимется PostgreSQL
if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  until python -c "import socket,os; socket.create_connection((os.environ['POSTGRES_HOST'], int(os.environ.get('POSTGRES_PORT', 5432))), 2)" 2>/dev/null; do
    sleep 1
  done
fi

python manage.py migrate --noinput

exec "$@"
