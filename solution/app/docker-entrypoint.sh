#!/bin/bash

set -e

echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "Database is ready!"

# Запуск миграций
echo "Running database migrations..."
python -m alembic upgrade head

# Запуск приложения
echo "Starting application..."
exec python app.py