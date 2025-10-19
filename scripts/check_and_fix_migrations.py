import os
import sys
from sqlalchemy import create_engine, text, inspect

def check_and_fix_migrations():
    database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            print(f"Found {len(existing_tables)} existing tables")
            
            # Проверяем существование ENUM типов
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sex_enum')"))
            sex_enum_exists = result.scalar()
            print(f"sex_enum exists: {sex_enum_exists}")
            
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_enum')"))
            status_enum_exists = result.scalar()
            print(f"status_enum exists: {status_enum_exists}")
            
            # Основные таблицы приложения
            core_tables = ['doctors', 'patients', 'consultations']
            core_tables_exist = all(table in existing_tables for table in core_tables)
            alembic_table_exists = 'alembic_version' in existing_tables
            
            # Сценарий 1: Таблицы есть, но alembic_version отсутствует
            if core_tables_exist and not alembic_table_exists:
                print("Tables exist but alembic_version missing - fixing...")
                conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
                
                # Находим последнюю миграцию
                migrations_dir = "migrations/versions"
                if os.path.exists(migrations_dir):
                    migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
                    if migration_files:
                        latest_migration = sorted(migration_files)[-1]
                        revision_id = latest_migration.split('_')[0]
                        conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{revision_id}')"))
                        conn.commit()
                        print(f"Marked migration {revision_id} as applied")
                return True
                
            # Сценарий 2: Пустая база - все нормально, миграции создадут таблицы
            elif not core_tables_exist and not alembic_table_exists:
                print("Fresh database - ready for migrations")
                return True
                
            # Сценарий 3: Alembic версия есть - все нормально
            elif alembic_table_exists:
                result = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                version = result.scalar()
                print(f"Alembic version: {version}")
                return True
                
    except Exception as e:
        print(f"Migration check failed: {e}")
        return False

if __name__ == "__main__":
    success = check_and_fix_migrations()
    sys.exit(0 if success else 1)