from flask import Flask, render_template, session, redirect, url_for, request, jsonify
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

# Импортируем AuthService после определения путей
import sys
sys.path.append(os.path.join(base_dir))
from services.auth_service import AuthService

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
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login')
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/registration')
def registration():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template('registration.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/edit')
@login_required
def edit_profile():
    return render_template('edit-profile.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Остальные маршруты остаются без изменений
@app.route('/consultation')
def consultation():
    return render_template('consultation/consultation.html')

@app.route('/consultation/result')
def consultation_result():
    return render_template('consultation/consultation-result.html')

@app.route('/consultation/history')
def consultation_history():
    return render_template('consultation/consultation-history.html')

# Пациенты
@app.route('/patient')
def patient_list():
    return render_template('patient/patients.html')

@app.route('/patient/new')
def patient_new():
    # Передаем текущую дату для ограничения даты рождения
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('patient/patient-new.html', today=today)

@app.route('/patient/history')
def patient_history():
    return render_template('patient/patient-history.html')

# Диагностика
@app.route('/diagnosis/questions')
def diagnosis_questions():
    return render_template('questions.html')

@app.route('/diagnosis/result')
def diagnosis_result():
    return render_template('diagnosis-result.html')

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

if __name__ == '__main__':
    print("=== Starting Flask Application ===")
    print(f"Base directory: {base_dir}")
    print(f"Template folder: {template_dir}")
    print(f"Static folder: {static_dir}")
    print(f"Templates exist: {os.path.exists(template_dir)}")
    print(f"Static exists: {os.path.exists(static_dir)}")
    print(f"CSS exists: {os.path.exists(os.path.join(static_dir, 'css', 'main.css'))}")
    print(f"Index.html exists: {os.path.exists(os.path.join(template_dir, 'index.html'))}")
    print(f"Patient-new.html exists: {os.path.exists(os.path.join(template_dir, 'patient-new.html'))}")
    app.run(host='0.0.0.0', port=5000, debug=True)