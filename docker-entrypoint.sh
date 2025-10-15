#!/bin/bash
set -e

echo "Starting application initialization..."

# Даем время базе данных запуститься
echo "Waiting for database..."
sleep 10

echo "Database should be ready, proceeding with setup..."

# Инициализируем базу данных (создает таблицы если их нет)
echo "Initializing database..."
python scripts/init_db.py

# Запускаем миграции (не блокируем запуск при ошибках)
echo "Running migrations..."
if python scripts/migrate.py; then
    echo "Migrations applied successfully"
else
    echo "Migrations skipped or already applied"
fi

# Запускаем основное приложение
echo "Starting Flask application..."
exec python solution/app/app.py