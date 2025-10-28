import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps
from flask import session, jsonify

def get_database_url():
    """Получение URL базы данных из переменных окружения"""
    return os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")

def get_db_session():
    """Создание сессии БД"""
    database_url = get_database_url()
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def login_required(f):
    """Декоратор для проверки авторизации"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Требуется авторизация'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def _calculate_age(birthday):
    """Расчет возраста по дате рождения"""
    from datetime import date
    today = date.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))