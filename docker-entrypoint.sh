#!/bin/bash

# Ожидание доступности базы данных
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Connection to db 5432 port [tcp/postgresql] succeeded!"
echo "Database is ready!"

# Проверка и фикс состояния миграций
echo "Checking and fixing migration state..."
python scripts/check_and_fix_migrations.py

# Запуск миграций Alembic с обработкой ошибок
echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations completed successfully"
else
    echo "Migration had issues, checking if tables exist..."
    # Проверяем, существуют ли основные таблицы
    python -c "
import os
from sqlalchemy import create_engine, text

database_url = os.getenv('DATABASE_URL', 'postgresql://admin:password@db:5432/ophthalmology_db')
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        # Проверяем существование основных таблиц
        tables = ['doctors', 'patients', 'consultations']
        existing_tables = []
        
        for table in tables:
            result = conn.execute(text(f\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')\"))
            if result.scalar():
                existing_tables.append(table)
        
        print(f'Existing tables: {existing_tables}')
        
        if len(existing_tables) == len(tables):
            print('All required tables exist - continuing...')
            exit(0)
        else:
            print(f'Missing tables. Need: {tables}, Have: {existing_tables}')
            exit(1)
            
except Exception as e:
    print(f'Error checking tables: {e}')
    exit(1)
    "
    
    if [ $? -eq 0 ]; then
        echo "Continuing with application startup..."
    else
        echo "Critical error: required tables are missing"
        exit 1
    fi
fi

# Запуск приложения
echo "Starting application..."
exec python solution/app/app.py