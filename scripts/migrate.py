import os
import sys
import time
from alembic.config import Config
from alembic import command

def wait_for_database():
    """Простая задержка для базы данных"""
    print("Waiting for database to be ready...")
    time.sleep(5)

def run_migrations():
    try:
        # Ждем базу данных
        wait_for_database()
        
        # Получаем путь к alembic.ini
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini_path = os.path.join(base_dir, 'alembic.ini')
        
        # Создаем конфиг Alembic
        alembic_cfg = Config(alembic_ini_path)
        
        # Запускаем миграции
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()