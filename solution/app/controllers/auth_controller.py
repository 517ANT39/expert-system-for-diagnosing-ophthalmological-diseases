from flask import Blueprint, request, jsonify, session, render_template
from utils.database import get_db_session, login_required
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

def _get_auth_service():
    """Вспомогательная функция для получения сервиса аутентификации"""
    db_session = get_db_session()
    return AuthService(db_session), db_session

def _json_response(success, message, data=None, status_code=200):
    """Универсальный метод для JSON ответов"""
    response = {'success': success, 'message': message}
    if data:
        response.update(data)
    return jsonify(response), status_code

def _update_session(doctor):
    """Обновление данных в сессии"""
    session.update({
        'doctor_id': doctor.id,
        'doctor_email': doctor.email,
        'doctor_name': f"{doctor.last_name} {doctor.first_name}",
        'logged_in': True
    })

# Страницы аутентификации
@auth_bp.route('/registration', methods=['GET'])
def registration_page():
    return render_template('registration.html')

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# API маршруты
@auth_bp.route('/api/register', methods=['POST'])
def register():
    try:
        auth_service, db_session = _get_auth_service()
        data = request.get_json()
        
        if data.get('password') != data.get('confirm_password'):
            return _json_response(False, 'Пароли не совпадают', status_code=400)
        
        doctor = auth_service.register_doctor(data)
        db_session.close()
        
        return _json_response(True, 'Регистрация успешна', 
                            {'doctor': doctor.to_dict()}, 201)
        
    except ValueError as e:
        return _json_response(False, str(e), status_code=400)
    except Exception as e:
        return _json_response(False, 'Ошибка сервера при регистрации', status_code=500)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        auth_service, db_session = _get_auth_service()
        data = request.get_json()
        
        doctor = auth_service.login_doctor(data.get('email'), data.get('password'))
        _update_session(doctor)
        db_session.close()
        
        return _json_response(True, 'Вход выполнен успешно', 
                            {'doctor': doctor.to_dict()})
        
    except ValueError as e:
        return _json_response(False, str(e), status_code=401)
    except Exception as e:
        return _json_response(False, 'Ошибка сервера при входе', status_code=500)

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return _json_response(True, 'Выход выполнен успешно')

@auth_bp.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    try:
        auth_service, db_session = _get_auth_service()
        doctor = auth_service.get_doctor_profile(session['doctor_id'])
        
        if not doctor:
            session.clear()
            return _json_response(False, 'Пользователь не найден', status_code=404)
        
        db_session.close()
        return _json_response(True, 'Профиль получен', {'doctor': doctor.to_dict()})
        
    except Exception as e:
        return _json_response(False, 'Ошибка сервера', status_code=500)