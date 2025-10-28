from flask import request, session, render_template
from utils.database import get_db_session, login_required, _calculate_age
from sqlalchemy.orm import joinedload
from models.database_models import Consultation, Patient
from services.patient_service import PatientService
from utils.controller_helpers import json_response, prepare_patient_data

def _get_patient_service():
    """Вспомогательная функция для получения сервиса пациентов"""
    db_session = get_db_session()
    return PatientService(db_session), db_session

def patient_controller(app):
    """Регистрация маршрутов для работы с пациентами"""

    @app.route('/patients')
    @login_required
    def patient_list():
        """Страница списка пациентов"""
        patient_service, db_session = _get_patient_service()
        try:
            patients = patient_service.get_all_patients()
            
            # Добавляем возраст для отображения
            for patient in patients:
                if patient.birthday:
                    patient.age = _calculate_age(patient.birthday)
                else:
                    patient.age = None
            
            return render_template('patient/patients.html', patients=patients)
            
        except Exception as e:
            print(f"Ошибка при загрузке списка пациентов: {str(e)}")
            return render_template('patient/patients.html', patients=[])
        finally:
            db_session.close()

    @app.route('/patient/<int:patient_id>/history')
    @login_required
    def patient_history(patient_id):
        """Страница истории пациента"""
        db_session = None
        try:
            db_session = get_db_session()
            
            patient = db_session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
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
            
            return render_template('patient/patient-history.html', 
                                 patient=patient, 
                                 consultations=consultations)
            
        except Exception as e:
            print(f"Ошибка при загрузке истории пациента: {str(e)}")
            return "Ошибка при загрузке страницы", 500
        finally:
            if db_session:
                db_session.close()

    @app.route('/api/patients/search')
    @login_required
    def api_search_patients():
        """Поиск пациентов через API"""
        patient_service, db_session = _get_patient_service()
        try:
            search_term = request.args.get('term', '')
            patients = patient_service.search_patients(search_term)
            
            patients_data = [prepare_patient_data(patient, for_json=True) for patient in patients]
            
            return json_response(True, 'Пациенты найдены', {
                'patients': patients_data,
                'total': len(patients_data)
            })
            
        except Exception as e:
            return json_response(False, f'Ошибка при поиске пациентов: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/patients', methods=['POST'])
    @login_required
    def api_create_patient():
        """Создание нового пациента"""
        patient_service, db_session = _get_patient_service()
        try:
            data = request.get_json()
            
            if not data:
                return json_response(False, 'Отсутствуют данные пациента', status_code=400)

            patient = patient_service.create_patient(data)
            
            return json_response(True, 'Пациент успешно создан', {
                'patient': prepare_patient_data(patient, for_json=True)
            }, 201)
            
        except ValueError as e:
            return json_response(False, str(e), status_code=400)
        except Exception as e:
            return json_response(False, f'Ошибка при создании пациента: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/patients', methods=['GET'])
    @login_required
    def api_get_patients():
        """Получение списка пациентов врача"""
        patient_service, db_session = _get_patient_service()
        try:
            doctor_id = session.get('doctor_id')
            search_term = request.args.get('search', '')
            
            patients = patient_service.get_doctor_patients(doctor_id)
            patients_data = [prepare_patient_data(patient, for_json=True) for patient in patients]
            
            return json_response(True, 'Пациенты получены', {
                'patients': patients_data,
                'total': len(patients_data)
            })
            
        except Exception as e:
            return json_response(False, f'Ошибка при получении списка пациентов: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/patients/<int:patient_id>', methods=['GET'])
    @login_required
    def api_get_patient(patient_id):
        """Получение информации о пациенте"""
        patient_service, db_session = _get_patient_service()
        try:
            patient = patient_service.get_patient(patient_id)
            
            if not patient:
                return json_response(False, 'Пациент не найден', status_code=404)
            
            return json_response(True, 'Данные пациента получены', {
                'patient': prepare_patient_data(patient, for_json=True)
            })
            
        except Exception as e:
            return json_response(False, f'Ошибка при получении данных пациента: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/patients/<int:patient_id>', methods=['PUT'])
    @login_required
    def api_update_patient(patient_id):
        """Обновление данных пациента"""
        patient_service, db_session = _get_patient_service()
        try:
            data = request.get_json()
            
            if not data:
                return json_response(False, 'Отсутствуют данные для обновления', status_code=400)

            patient = patient_service.update_patient(patient_id, data)
            
            if not patient:
                return json_response(False, 'Пациент не найден', status_code=404)
            
            return json_response(True, 'Данные пациента успешно обновлены', {
                'patient': prepare_patient_data(patient, for_json=True)
            })
            
        except ValueError as e:
            return json_response(False, str(e), status_code=400)
        except Exception as e:
            return json_response(False, f'Ошибка при обновлении данных пациента: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/patient/<int:patient_id>/edit')
    @login_required
    def edit_patient(patient_id):
        """Страница редактирования пациента"""
        db_session = None
        try:
            db_session = get_db_session()
            
            patient = db_session.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return "Пациент не найден", 404
            
            return render_template('patient/edit-patient.html', 
                                 patient=prepare_patient_data(patient, for_json=False))
            
        except Exception as e:
            print(f"Ошибка при загрузке страницы редактирования пациента: {str(e)}")
            return "Ошибка при загрузке страницы", 500
        finally:
            if db_session:
                db_session.close()