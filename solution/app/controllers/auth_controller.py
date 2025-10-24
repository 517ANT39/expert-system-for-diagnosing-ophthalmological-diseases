from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.auth_service import AuthService
import os

# Настройка базы данных
database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

auth_bp = Blueprint('auth', __name__)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@auth_bp.route('/registration', methods=['GET'])
def registration_page():
    return render_template('registration.html')

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth_bp.route('/api/register', methods=['POST'])
def register():
    try:
        db_session = SessionLocal()
        auth_service = AuthService(db_session)
        
        data = request.get_json()
        
        # Валидация подтверждения пароля
        if data.get('password') != data.get('confirm_password'):
            return jsonify({
                'success': False,
                'message': 'Пароли не совпадают'
            }), 400
        
        doctor = auth_service.register_doctor(data)
        
        db_session.close()
        
        return jsonify({
            'success': True,
            'message': 'Регистрация успешна',
            'doctor': doctor.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка сервера при регистрации'
        }), 500

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        db_session = SessionLocal()
        auth_service = AuthService(db_session)
        
        data = request.get_json()
        doctor = auth_service.login_doctor(data.get('email'), data.get('password'))
        
        # Сохраняем в сессии
        session['doctor_id'] = doctor.id
        session['doctor_email'] = doctor.email
        session['doctor_name'] = f"{doctor.last_name} {doctor.first_name}"
        session['logged_in'] = True
        
        db_session.close()
        
        return jsonify({
            'success': True,
            'message': 'Вход выполнен успешно',
            'doctor': doctor.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка сервера при входе'
        }), 500

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Выход выполнен успешно'
    }), 200

@auth_bp.route('/api/profile', methods=['GET'])
def get_profile():
    if not session.get('logged_in'):
        return jsonify({
            'success': False,
            'message': 'Не авторизован'
        }), 401
    
    try:
        db_session = SessionLocal()
        auth_service = AuthService(db_session)
        
        doctor = auth_service.get_doctor_profile(session['doctor_id'])
        
        if not doctor:
            session.clear()
            return jsonify({
                'success': False,
                'message': 'Пользователь не найден'
            }), 404
        
        db_session.close()
        
        return jsonify({
            'success': True,
            'doctor': doctor.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка сервера'
        }), 500