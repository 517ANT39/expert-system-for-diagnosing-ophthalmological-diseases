import os
import sys
from sqlalchemy import create_engine, text, inspect

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution.app.models.database_models import Base

def init_database():
    database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
    
    engine = create_engine(database_url)
    
    try:
        # Проверяем подключение
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return
    
    # Проверяем какие таблицы уже существуют
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")
    
    # Создаем только недостающие таблицы
    if not existing_tables:
        Base.metadata.create_all(engine)
        print("All tables created successfully")
    else:
        print("Tables already exist, skipping creation")

if __name__ == "__main__":
    init_database()