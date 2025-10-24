import os
from sqlalchemy import create_engine, text

def check_database():
    """Базовая проверка подключения к БД"""
    database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Простая проверка подключения
            conn.execute(text("SELECT 1"))
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    check_database()