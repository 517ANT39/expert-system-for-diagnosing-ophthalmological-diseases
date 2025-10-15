#!/bin/bash
set -e

echo "Waiting for database to be ready..."

# Простая задержка вместо nc проверки
sleep 10

echo "Database should be ready, proceeding with migrations..."

# Инициализируем базу данных
echo "Initializing database..."
python scripts/init_db.py

# Запускаем миграции
echo "Running migrations..."
python scripts/migrate.py

# Запускаем основное приложение
echo "Starting Flask application..."
exec python solution/app/app.py