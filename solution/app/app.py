from flask import Flask, render_template
import os
from datetime import datetime

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

# Все основные маршруты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

# Новый маршрут для редактирования профиля
@app.route('/profile/edit')
def edit_profile():
    return render_template('edit-profile.html')

# Консультации
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
    return render_template(patient/'patient-history.html')

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