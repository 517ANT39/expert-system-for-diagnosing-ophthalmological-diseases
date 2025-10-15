import os
import sys
from sqlalchemy import create_engine, text

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solution.app.models.database_models import Base

def init_database():
    database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
    
    engine = create_engine(database_url)
    
    try:
        # Проверяем подключение к базе
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return
    
    # Создаем таблицы
    try:
        Base.metadata.create_all(engine)
        print("Tables created successfully")
    except Exception as e:
        print(f"Table creation failed: {e}")

if __name__ == "__main__":
    init_database()