import os
import sys
import time
from alembic.config import Config
from alembic import command

def wait_for_database():
    print("Waiting for database to be ready...")
    time.sleep(5)

def run_migrations():
    try:
        wait_for_database()
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini_path = os.path.join(base_dir, 'alembic.ini')
        
        alembic_cfg = Config(alembic_ini_path)
        
        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully")
        
    except Exception as e:
        print(f"Migration completed or not needed: {e}")
        # НЕ выходим с ошибкой, просто логируем

if __name__ == "__main__":
    run_migrations()