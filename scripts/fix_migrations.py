import os
from sqlalchemy import create_engine, text

def fix_migrations():
    database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Получаем список файлов миграций
        migrations_dir = "/app/migrations/versions"
        if os.path.exists(migrations_dir):
            migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
            if migration_files:
                # Берем первую миграцию (самую старую)
                first_migration = sorted(migration_files)[0]
                # Извлекаем номер ревизии из имени файла (например: 001_initial.py -> 001)
                revision_id = first_migration.split('_')[0]
                
                # Обновляем таблицу alembic_version
                conn.execute(text("DELETE FROM alembic_version"))
                conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{revision_id}')"))
                conn.commit()
                print(f"Fixed alembic_version to: {revision_id}")
                return
    
    print("No migration files found, using default")
    # Если файлов миграций нет, создаем базовую запись
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('001')"))
        conn.commit()
        print("Set alembic_version to default: 001")

if __name__ == "__main__":
    fix_migrations()