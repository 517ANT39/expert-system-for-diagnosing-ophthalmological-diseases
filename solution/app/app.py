from flask import Flask, render_template, session, redirect, url_for, request, jsonify, make_response
import os
import bcrypt
from datetime import datetime
from weasyprint import HTML

# Импорты из utils
from utils.database import get_db_session, login_required, _calculate_age
from utils.consultation_helpers import prepare_consultation_data

# Импорты моделей и контроллеров
from models.database_models import Doctor, Consultation, Patient
from controllers.patient_controller import patient_controller
from services.auth_service import AuthService
from controllers.consultation_controller import consultation_controller

# Конфигурация путей
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'views', 'templates')
static_dir = os.path.join(base_dir, 'views', 'static')

app = Flask(__name__, 
    template_folder=template_dir,
    static_folder=static_dir
)

# Конфигурация приложения
app.secret_key = os.getenv('SECRET_KEY')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'

# Регистрируем контроллеры
consultation_controller(app)
patient_controller(app)

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
        'doctor_full_name': f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}".strip(),
        'logged_in': True
    })

# API маршруты для аутентификации
@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        auth_service, db_session = _get_auth_service()
        data = request.get_json()
        
        # Валидация пароля
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

@app.route('/api/login', methods=['POST'])
def api_login():
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

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return _json_response(True, 'Выход выполнен успешно')

@app.route('/api/profile')
@login_required
def api_profile():
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

# Основные маршруты
@app.route('/')
def index():
    return render_template('index.html', 
                         logged_in=session.get('logged_in', False),
                         doctor_name=session.get('doctor_name'))

def _redirect_if_authenticated(route):
    """Перенаправление если пользователь уже авторизован"""
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template(f'{route}.html')

@app.route('/login')
def login():
    return _redirect_if_authenticated('login')

@app.route('/registration')
def registration():
    return _redirect_if_authenticated('registration')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/edit')
@login_required
def edit_profile():
    return render_template('edit-profile.html')

# API для управления профилем
@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_profile_update():
    try:
        auth_service, db_session = _get_auth_service()
        data = request.get_json()
        doctor_id = session['doctor_id']
        
        doctor = auth_service.get_doctor_profile(doctor_id)
        if not doctor:
            return _json_response(False, 'Пользователь не найден', status_code=404)
        
        # Проверка уникальности email
        if 'email' in data and data['email'] != doctor.email:
            existing_doctor = db_session.query(Doctor).filter(
                Doctor.email == data['email'],
                Doctor.id != doctor_id
            ).first()
            if existing_doctor:
                return _json_response(False, 'Этот email уже используется другим пользователем', status_code=400)
        
        # Обновление данных
        update_fields = ['last_name', 'first_name', 'middle_name', 'email', 'phone']
        for field in update_fields:
            if field in data:
                setattr(doctor, field, data[field])
        
        db_session.commit()
        _update_session(doctor)
        db_session.close()
        
        return _json_response(True, 'Профиль успешно обновлен', 
                            {'doctor': doctor.to_dict()})
        
    except Exception as e:
        db_session.rollback()
        return _json_response(False, 'Ошибка сервера при обновлении профиля', status_code=500)

@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    try:
        auth_service, db_session = _get_auth_service()
        data = request.get_json()
        doctor_id = session['doctor_id']
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return _json_response(False, 'Текущий и новый пароль обязательны', status_code=400)
        
        doctor = auth_service.get_doctor_profile(doctor_id)
        if not doctor:
            return _json_response(False, 'Пользователь не найден', status_code=404)
        
        # Проверка текущего пароля
        if not auth_service.user_repository.verify_password(current_password, doctor.password):
            return _json_response(False, 'Неверный текущий пароль', status_code=400)
        
        # Валидация нового пароля
        if len(new_password) < 6:
            return _json_response(False, 'Новый пароль должен содержать минимум 6 символов', status_code=400)
        
        # Обновление пароля
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        doctor.password = hashed_password
        db_session.commit()
        db_session.close()
        
        return _json_response(True, 'Пароль успешно изменен')
        
    except Exception as e:
        db_session.rollback()
        return _json_response(False, 'Ошибка сервера при смене пароля', status_code=500)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/patient/new')
@login_required
def patient_new():
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('patient/patient-new.html', today=today)

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        db_session = get_db_session()
        patients = db_session.query(Patient).all()
        
        # Добавляем возраст для отображения
        for patient in patients:
            patient.age = _calculate_age(patient.birthday) if patient.birthday else None
        
        db_session.close()
        return render_template('dashboard.html', patients=patients)
        
    except Exception as e:
        print(f"Ошибка при загрузке dashboard: {str(e)}")
        return render_template('dashboard.html', patients=[])

@app.route('/consultation/<int:consultation_id>/export-pdf')
@login_required
def export_consultation_pdf(consultation_id):
    try:
        db_session = get_db_session()
        consultation = db_session.query(Consultation).filter_by(id=consultation_id).first()
        
        if not consultation:
            db_session.close()
            return "Консультация не найдена", 404
        
        patient = consultation.patient
        doctor = consultation.doctor
        diagnosis_result = prepare_consultation_data(consultation)
        
        # Расчет возраста
        birth_date = patient.birthday
        today = datetime.now().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        # Генерация PDF
        html_content = render_template('pdf_consultation.html',
            consultation=consultation,
            patient={
                'name': f"{patient.last_name} {patient.first_name} {patient.middle_name or ''}",
                'birth_date': patient.birthday.strftime('%d.%m.%Y'),
                'age': age,
                'sex': patient.sex
            },
            doctor={'name': f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}"},
            diagnosis_result=diagnosis_result,
            current_date=datetime.now().strftime('%d.%m.%Y')
        )
        
        pdf_file = HTML(string=html_content).write_pdf()
        
        response = make_response(pdf_file)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=consultation_{consultation_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        db_session.close()
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return "Ошибка при генерации PDF", 500

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    debug_mode = app.config['DEBUG']
    app.run(host='0.0.0.0', port=8080, debug=debug_mode)