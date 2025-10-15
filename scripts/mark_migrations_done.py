import os
from sqlalchemy import create_engine, text

def mark_migrations_done():
    """Помечаем что миграции уже выполнены вручную"""
    database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Проверяем существует ли таблица alembic_version
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'alembic_version'
            )
        """))
        exists = result.scalar()
        
        if not exists:
            # Создаем таблицу и помечаем миграции как выполненные
            conn.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL
                )
            """))
            conn.execute(text("""
                INSERT INTO alembic_version (version_num) VALUES ('manual_setup')
            """))
            conn.commit()
            print("Marked migrations as manually completed")
        else:
            print("Migrations already marked as completed")

if __name__ == "__main__":
    mark_migrations_done()