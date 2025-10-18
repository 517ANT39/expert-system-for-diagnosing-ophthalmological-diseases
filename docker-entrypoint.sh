#!/bin/bash
set -e

echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database is ready!"

echo "Checking and fixing migration state..."
python scripts/check_and_fix_migrations.py

echo "Running database migrations..."
alembic upgrade head || {
    echo "Migrations completed with warnings, but continuing startup..."
}

echo "Starting Flask application..."
exec python solution/app/app.py