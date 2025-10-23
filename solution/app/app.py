from flask import Flask, render_template, session, redirect, url_for, request, jsonify
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import make_response
from weasyprint import HTML
import tempfile

# Добавляем путь к корню проекта в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

# Абсолютные импорты с полным путем
from solution.app.models.database_models import Doctor, Consultation, Patient
from solution.app.controllers.patient_controller import patient_controller
from solution.app.services.auth_service import AuthService
from solution.app.services.patient_service import PatientService
from solution.app.controllers.consultation_controller import consultation_controller
from solution.app.controllers.patient_controller import get_db_session, _calculate_age

# В Docker рабочая директория /app, поэтому пути другие
base_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Base dir: {base_dir}")

# Правильные пути для Docker
template_dir = os.path.join(base_dir, 'views', 'templates')
static_dir = os.path.join(base_dir, 'views', 'static')

app = Flask(__name__, 
    template_folder=template_dir,
    static_folder=static_dir
)

# Конфигурация
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'

# Настройка базы данных
database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

consultation_controller(app)

def login_required(f):
    """Декоратор для проверки авторизации"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# API маршруты для аутентификации
@app.route('/api/register', methods=['POST'])
def api_register():
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

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        db_session = SessionLocal()
        auth_service = AuthService(db_session)
        
        data = request.get_json()
        doctor = auth_service.login_doctor(data.get('email'), data.get('password'))
        
        # Сохраняем в сессии
        session['doctor_id'] = doctor.id
        session['doctor_email'] = doctor.email
        session['doctor_name'] = f"{doctor.last_name} {doctor.first_name}"
        session['doctor_full_name'] = f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}".strip()
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

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Выход выполнен успешно'
    }), 200

@app.route('/api/profile')
@login_required
def api_profile():
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

# Основные маршруты с проверкой авторизации
@app.route('/')
def index():
    # Главная страница доступна всем - и авторизованным и неавторизованным
    # Передаем информацию о авторизации в шаблон
    return render_template('index.html', 
                         logged_in=session.get('logged_in', False),
                         doctor_name=session.get('doctor_name'))

@app.route('/login')
def login():
    # Если уже авторизован - перенаправляем на dashboard
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/registration')
def registration():
    # Если уже авторизован - перенаправляем на dashboard
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('registration.html')

# Регистрируем контроллер пациентов
patient_controller(app)

#@app.route('/dashboard')
#@login_required
#def dashboard():
    #return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/edit')
@login_required
def edit_profile():
    return render_template('edit-profile.html')

# API для обновления профиля
@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_profile_update():
    try:
        db_session = SessionLocal()
        auth_service = AuthService(db_session)
        
        data = request.get_json()
        doctor_id = session['doctor_id']
        
        # Получаем текущего врача
        doctor = auth_service.get_doctor_profile(doctor_id)
        if not doctor:
            return jsonify({
                'success': False,
                'message': 'Пользователь не найден'
            }), 404
        
        # Обновляем данные
        if 'last_name' in data:
            doctor.last_name = data['last_name']
        if 'first_name' in data:
            doctor.first_name = data['first_name']
        if 'middle_name' in data:
            doctor.middle_name = data['middle_name']
        if 'email' in data:
            # Проверяем, не занят ли email другим пользователем
            existing_doctor = db_session.query(Doctor).filter(
                Doctor.email == data['email'],
                Doctor.id != doctor_id
            ).first()
            if existing_doctor:
                return jsonify({
                    'success': False,
                    'message': 'Этот email уже используется другим пользователем'
                }), 400
            doctor.email = data['email']
        if 'phone' in data:
            doctor.phone = data['phone']
        
        db_session.commit()
        
        # Обновляем сессию
        session['doctor_name'] = f"{doctor.last_name} {doctor.first_name}"
        session['doctor_full_name'] = f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}".strip()
        
        db_session.close()
        
        return jsonify({
            'success': True,
            'message': 'Профиль успешно обновлен',
            'doctor': doctor.to_dict()
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'message': 'Ошибка сервера при обновлении профиля'
        }), 500

# API для смены пароля
@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    try:
        db_session = SessionLocal()
        auth_service = AuthService(db_session)
        
        data = request.get_json()
        doctor_id = session['doctor_id']
        
        # Проверяем обязательные поля
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': 'Текущий и новый пароль обязательны'
            }), 400
        
        # Получаем текущего врача
        doctor = auth_service.get_doctor_profile(doctor_id)
        if not doctor:
            return jsonify({
                'success': False,
                'message': 'Пользователь не найден'
            }), 404
        
        # Проверяем текущий пароль
        if not auth_service.user_repository.verify_password(data['current_password'], doctor.password):
            return jsonify({
                'success': False,
                'message': 'Неверный текущий пароль'
            }), 400
        
        # Проверяем длину нового пароля
        if len(data['new_password']) < 6:
            return jsonify({
                'success': False,
                'message': 'Новый пароль должен содержать минимум 6 символов'
            }), 400
        
        # Хешируем и сохраняем новый пароль
        import bcrypt
        hashed_password = bcrypt.hashpw(
            data['new_password'].encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        doctor.password = hashed_password
        db_session.commit()
        db_session.close()
        
        return jsonify({
            'success': True,
            'message': 'Пароль успешно изменен'
        }), 200
        
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'message': 'Ошибка сервера при смене пароля'
        }), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))  # После выхода - на главную страницу

# Защищенные маршруты (требуют авторизации)
#@app.route('/consultation')
#@login_required
#def consultation():
   # return render_template('consultation/consultation.html')
"""
@app.route('/consultation/result')
@login_required
def consultation_result():
    return render_template('consultation/consultation-result.html')

@app.route('/consultation/history')
@login_required
def consultation_history():
    return render_template('consultation/consultation-history.html')"""

"""
# Пациенты (требуют авторизации)
@app.route('/patient')
@login_required
def patient_list():
    return render_template('patient/patients.html')

@app.route('/patients')
@login_required
def patient_list():
    #Страница списка пациентов
    try:
        db_session = get_db_session()
        patient_service = PatientService(db_session)
        
        # Получаем всех пациентов напрямую из таблицы patients
        patients = patient_service.get_all_patients()
        
        # Добавляем возраст для отображения
        for patient in patients:
            if patient.birthday:
                patient.age = _calculate_age(patient.birthday)
            else:
                patient.age = None
        
        db_session.close()
        
        return render_template('patient.html', patients=patients)
        
    except Exception as e:
        print(f"Ошибка при загрузке списка пациентов: {str(e)}")
        # В случае ошибки показываем пустой список
        return render_template('patient.html', patients=[])
    
@app.route('/api/patients/search')
@login_required
def api_search_patients():
    #Поиск пациентов через API
    db_session = None
    try:
        db_session = get_db_session()
        patient_service = PatientService(db_session)
        
        search_term = request.args.get('term', '')
        patients = patient_service.search_patients(search_term)
        
        # Форматируем ответ
        patients_data = []
        for patient in patients:
            patients_data.append({
                'id': patient.id,
                'last_name': patient.last_name,
                'first_name': patient.first_name,
                'middle_name': patient.middle_name,
                'birthday': patient.birthday.isoformat() if patient.birthday else None,
                'sex': patient.sex.value,
                'phone': patient.phone,
                'email': patient.email,
                'age': _calculate_age(patient.birthday) if patient.birthday else None,
                'registered_at': patient.registered_at.isoformat() if patient.registered_at else None
            })
        
        return jsonify({
            'success': True,
            'patients': patients_data,
            'total': len(patients_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при поиске пациентов: {str(e)}'
        }), 500
    finally:
        if db_session:
            db_session.close()
            """

@app.route('/patient/new')
@login_required
def patient_new():
    # Передаем текущую дату для ограничения даты рождения
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('patient/patient-new.html', today=today)

# Диагностика (требуют авторизации)
@app.route('/diagnosis/questions')
@login_required
def diagnosis_questions():
    return render_template('diagnosis/questions.html')

@app.route('/diagnosis/result')
@login_required
def diagnosis_result():
    return render_template('diagnosis/result.html')

# ... существующий код ...

@app.route('/dashboard')
@login_required
def dashboard():
    """Главная панель управления"""
    try:
        db_session = get_db_session()
        
        # Получаем всех пациентов напрямую из таблицы patients
        patients = db_session.query(Patient).all()
        
        # Добавляем возраст для отображения
        for patient in patients:
            if patient.birthday:
                patient.age = _calculate_age(patient.birthday)
            else:
                patient.age = None
        
        db_session.close()
        
        return render_template('dashboard.html', patients=patients)
        
    except Exception as e:
        print(f"Ошибка при загрузке dashboard: {str(e)}")
        # В случае ошибки показываем пустой список
        return render_template('dashboard.html', patients=[])
    
@app.route('/consultation/<int:consultation_id>/export-pdf')
@login_required
def export_consultation_pdf(consultation_id):
    try:
        # Используем существующую сессию базы данных
        db_session = SessionLocal()
        
        # Получаем данные консультации
        consultation = db_session.query(Consultation).filter_by(id=consultation_id).first()
        if not consultation:
            db_session.close()
            return "Консультация не найдена", 404
        
        patient = consultation.patient
        doctor = consultation.doctor
        
        # Получаем данные диагностики
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        
        # Формируем данные для PDF
        diagnosis_result = {
            'primary_diagnosis': consultation.final_diagnosis or diagnosis_data.get('primary_diagnosis', 'Диагноз не указан'),
            'symptoms_evidence': diagnosis_data.get('symptoms_evidence', []),
            'recommendations': diagnosis_data.get('recommendations', {})
        }
        
        # Рассчитываем возраст пациента
        birth_date = patient.birthday
        today = datetime.now().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        # Формируем HTML для PDF
        html_content = render_template('pdf_consultation.html',
            consultation=consultation,
            patient={
                'name': f"{patient.last_name} {patient.first_name} {patient.middle_name or ''}",
                'birth_date': patient.birthday.strftime('%d.%m.%Y'),
                'age': age,
                'sex': patient.sex
            },
            doctor={
                'name': f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}"
            },
            diagnosis_result=diagnosis_result,
            current_date=datetime.now().strftime('%d.%m.%Y')
        )
        
        # Создаем PDF
        html = HTML(string=html_content)
        pdf_file = html.write_pdf()
        
        # Создаем response
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

# Debug route
@app.route('/debug')
def debug():
    return f"""
    <h1>Debug Information</h1>
    <p>Base dir: {base_dir}</p>
    <p>Template folder: {template_dir}</p>
    <p>Static folder: {static_dir}</p>
    <p>Templates exist: {os.path.exists(template_dir)}</p>
    <p>Static exists: {os.path.exists(static_dir)}</p>
    <p>CSS exists: {os.path.exists(os.path.join(static_dir, 'css', 'main.css'))}</p>
    <p>Index.html exists: {os.path.exists(os.path.join(template_dir, 'index.html'))}</p>
    <p>Patient-new.html exists: {os.path.exists(os.path.join(template_dir, 'patient-new.html'))}</p>
    <p>User logged in: {session.get('logged_in', False)}</p>
    <p>User ID: {session.get('doctor_id')}</p>
    <p>User name: {session.get('doctor_name')}</p>
    """

@app.route('/debug/consultation/<int:consultation_id>')
@login_required
def debug_consultation(consultation_id):
    """Диагностический маршрут для проверки консультации"""
    try:
        db_session = get_db_session()
        from solution.app.services.consultation_service import ConsultationService
        from solution.app.services.diagnosis_service import DiagnosisService
        
        consultation_service = ConsultationService(db_session)
        diagnosis_service = DiagnosisService()
        
        consultation = consultation_service.consultation_repository.get_consultation_by_id(consultation_id)
        
        result = {
            'consultation': {
                'id': consultation.id,
                'status': consultation.status,
                'sub_graph_find_diagnosis': consultation.sub_graph_find_diagnosis
            },
            'knowledge_graph_loaded': bool(diagnosis_service.knowledge_graph),
            'initial_question': diagnosis_service.get_initial_question(),
            'current_question': consultation_service.get_current_question(consultation_id)
        }
        
        db_session.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/debug/services')
def debug_services():
    """Проверка версий сервисов"""
    import importlib
    import solution.app.services.consultation_service as cs
    import solution.app.services.diagnosis_service as ds
    
    return jsonify({
        'consultation_service_file': cs.__file__,
        'diagnosis_service_file': ds.__file__,
        'consultation_service_reload': importlib.reload(cs).__file__,
        'diagnosis_service_reload': importlib.reload(ds).__file__
    })

@app.route('/debug/db/consultation/<int:consultation_id>')
@login_required
def debug_db_consultation(consultation_id):
    """Проверка данных консультации в БД"""
    try:
        db_session = get_db_session()
        consultation = db_session.query(Consultation).filter(Consultation.id == consultation_id).first()
        
        if consultation:
            result = {
                'id': consultation.id,
                'status': consultation.status,
                'sub_graph_find_diagnosis': consultation.sub_graph_find_diagnosis,
                'raw_data': str(consultation.sub_graph_find_diagnosis)  # Для отладки
            }
        else:
            result = {'error': 'Consultation not found'}
        
        db_session.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=== Starting Flask Application ===")
    print(f"Base directory: {base_dir}")
    print(f"Template folder: {template_dir}")
    print(f"Static footer: {static_dir}")
    print(f"Templates exist: {os.path.exists(template_dir)}")
    print(f"Static exists: {os.path.exists(static_dir)}")
    print(f"CSS exists: {os.path.exists(os.path.join(static_dir, 'css', 'main.css'))}")
    print(f"Index.html exists: {os.path.exists(os.path.join(template_dir, 'index.html'))}")
    print(f"Patient-new.html exists: {os.path.exists(os.path.join(template_dir, 'patient-new.html'))}")
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='0.0.0.0', port=5000, debug=False) при сдаче изменить на False