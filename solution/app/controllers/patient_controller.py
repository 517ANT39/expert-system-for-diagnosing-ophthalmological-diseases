from flask import request, jsonify, session, render_template
from utils.database import get_db_session, login_required, _calculate_age
from sqlalchemy.orm import joinedload
from models.database_models import Consultation, Patient
from services.patient_service import PatientService

def patient_controller(app):
    """Регистрация маршрутов для работы с пациентами"""
    
    # HTML маршрут для страницы пациентов
    @app.route('/patients')
    @login_required
    def patient_list():
        """Страница списка пациентов"""
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
            
            return render_template('patient/patients.html', patients=patients)
            
        except Exception as e:
            print(f"Ошибка при загрузке списка пациентов: {str(e)}")
            # В случае ошибки показываем пустой список
            return render_template('patient/patients.html', patients=[])
    
    # HTML маршрут для страницы истории пациента
    @app.route('/patient/<int:patient_id>/history')
    @login_required
    def patient_history(patient_id):
        """Страница истории пациента"""
        db_session = None
        try:
            db_session = get_db_session()
            
            # Получаем данные пациента
            patient = db_session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                db_session.close()
                return "Пациент не найден", 404
            
            # Добавляем возраст для отображения
            if patient.birthday:
                patient.age = _calculate_age(patient.birthday)
            else:
                patient.age = None
            
            # Получаем консультации пациента
            consultations = db_session.query(Consultation).options(
                joinedload(Consultation.doctor)
            ).filter(
                Consultation.patient_id == patient_id
            ).order_by(
                Consultation.consultation_date.desc()
            ).all()
            
            db_session.close()
            
            return render_template('patient/patient-history.html', 
                                 patient=patient, 
                                 consultations=consultations)
            
        except Exception as e:
            print(f"Ошибка при загрузке истории пациента: {str(e)}")
            if db_session:
                db_session.close()
            return "Ошибка при загрузке страницы", 500
    
    # API маршрут для поиска пациентов
    @app.route('/api/patients/search')
    @login_required
    def api_search_patients():
        """Поиск пациентов через API"""
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
                    'sex': patient.sex,
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
    
    # Остальные API маршруты...
    @app.route('/api/patients', methods=['POST'])
    @login_required
    def api_create_patient():
        """Создание нового пациента"""
        db_session = None
        try:
            db_session = get_db_session()
            patient_service = PatientService(db_session)
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Отсутствуют данные пациента'
                }), 400

            # Создаем пациента
            patient = patient_service.create_patient(data)
            
            return jsonify({
                'success': True,
                'message': 'Пациент успешно создан',
                'patient': {
                    'id': patient.id,
                    'last_name': patient.last_name,
                    'first_name': patient.first_name,
                    'middle_name': patient.middle_name,
                    'birthday': patient.birthday.isoformat() if patient.birthday else None,
                    'sex': patient.sex,
                    'phone': patient.phone,
                    'email': patient.email,
                    'address': patient.address,
                    'registered_at': patient.registered_at.isoformat() if patient.registered_at else None
                }
            }), 201
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Ошибка при создании пациента: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    @app.route('/api/patients', methods=['GET'])
    @login_required
    def api_get_patients():
        """Получение списка пациентов врача"""
        db_session = None
        try:
            db_session = get_db_session()
            patient_service = PatientService(db_session)
            
            doctor_id = session.get('doctor_id')
            search_term = request.args.get('search', '')
            
            patients = patient_service.get_doctor_patients(doctor_id)
            
            # Форматируем ответ
            patients_data = []
            for patient in patients:
                patients_data.append({
                    'id': patient.id,
                    'last_name': patient.last_name,
                    'first_name': patient.first_name,
                    'middle_name': patient.middle_name,
                    'birthday': patient.birthday.isoformat() if patient.birthday else None,
                    'sex': patient.sex,
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
                'message': f'Ошибка при получении списка пациентов: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    @app.route('/api/patients/<int:patient_id>', methods=['GET'])
    @login_required
    def api_get_patient(patient_id):
        """Получение информации о пациенте"""
        db_session = None
        try:
            db_session = get_db_session()
            patient_service = PatientService(db_session)
            
            patient = patient_service.get_patient(patient_id)
            
            if not patient:
                return jsonify({
                    'success': False,
                    'message': 'Пациент не найден'
                }), 404
            
            return jsonify({
                'success': True,
                'patient': {
                    'id': patient.id,
                    'last_name': patient.last_name,
                    'first_name': patient.first_name,
                    'middle_name': patient.middle_name,
                    'birthday': patient.birthday.isoformat() if patient.birthday else None,
                    'sex': patient.sex,
                    'phone': patient.phone,
                    'email': patient.email,
                    'address': patient.address,
                    'allergies': patient.allergies,
                    'chronic_diseases': patient.chronic_diseases,
                    'current_medications': patient.current_medications,
                    'family_anamnes': patient.family_anamnes,
                    'notes': patient.notes,
                    'registered_at': patient.registered_at.isoformat() if patient.registered_at else None
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Ошибка при получении данных пациента: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    @app.route('/api/patients/<int:patient_id>', methods=['PUT'])
    @login_required
    def api_update_patient(patient_id):
        """Обновление данных пациента"""
        db_session = None
        try:
            db_session = get_db_session()
            patient_service = PatientService(db_session)
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Отсутствуют данные для обновления'
                }), 400

            patient = patient_service.update_patient(patient_id, data)
            
            if not patient:
                return jsonify({
                    'success': False,
                    'message': 'Пациент не найден'
                }), 404
            
            return jsonify({
                'success': True,
                'message': 'Данные пациента успешно обновлены',
                'patient': {
                    'id': patient.id,
                    'last_name': patient.last_name,
                    'first_name': patient.first_name,
                    'middle_name': patient.middle_name,
                    'birthday': patient.birthday.isoformat() if patient.birthday else None,
                    'sex': patient.sex,
                    'phone': patient.phone,
                    'email': patient.email,
                    'address': patient.address,
                    'allergies': patient.allergies,
                    'chronic_diseases': patient.chronic_diseases,
                    'current_medications': patient.current_medications,
                    'family_anamnes': patient.family_anamnes,
                    'notes': patient.notes
                }
            }), 200
            
        except ValueError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Ошибка при обновлении данных пациента: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    @app.route('/patient/<int:patient_id>/edit')
    @login_required
    def edit_patient(patient_id):
        """Страница редактирования пациента"""
        db_session = None
        try:
            db_session = get_db_session()
            
            # Получаем данные пациента
            patient = db_session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                db_session.close()
                return "Пациент не найден", 404
            
            db_session.close()
            
            # Рендерим шаблон редактирования пациента
            return render_template('patient/edit-patient.html', patient=patient)
            
        except Exception as e:
            print(f"Ошибка при загрузке страницы редактирования пациента: {str(e)}")
            if db_session:
                db_session.close()
            return "Ошибка при загрузке страницы", 500