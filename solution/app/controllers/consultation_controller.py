from flask import request, jsonify, session, render_template
from services.consultation_service import ConsultationService, get_diagnosis_service
from utils.database import get_db_session, login_required, _calculate_age
from utils.consultation_helpers import prepare_consultation_data
from models.database_models import Consultation
from sqlalchemy.orm import joinedload
import os

# Предварительная инициализация сервиса
_diagnosis_service = get_diagnosis_service()

def _get_consultation_service():
    """Вспомогательная функция для получения сервиса консультаций"""
    db_session = get_db_session()
    return ConsultationService(db_session), db_session

def _json_response(success, message, data=None, status_code=200):
    """Универсальный метод для JSON ответов"""
    response = {'success': success, 'message': message}
    if data:
        response.update(data)
    return jsonify(response), status_code

def _prepare_patient_data(patient):
    """Подготовка данных пациента для шаблона"""
    return {
        'id': patient.id,
        'last_name': patient.last_name,
        'first_name': patient.first_name,
        'middle_name': patient.middle_name,
        'birthday': patient.birthday,
        'age': _calculate_age(patient.birthday) if patient.birthday else None
    }

def _prepare_consultation_result_data(consultation_data, diagnosis_result):
    """Подготовка данных для страницы результатов консультации"""
    patient = consultation_data.patient
    doctor = consultation_data.doctor
    
    from datetime import datetime
    return {
        'patient': {
            'name': f"{patient.last_name} {patient.first_name} {patient.middle_name or ''}".strip(),
            'birth_date': patient.birthday.strftime('%d.%m.%Y') if patient.birthday else 'Не указана',
            'sex': patient.sex,
            'age': _calculate_age(patient.birthday) if patient.birthday else None
        },
        'doctor': {
            'name': f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}".strip(),
            'qualification': "Врач-офтальмолог"
        },
        'consultation_info': {
            'date': consultation_data.consultation_date.strftime('%d.%m.%Y %H:%M') if consultation_data.consultation_date else datetime.now().strftime('%d.%m.%Y %H:%M'),
            'final_diagnosis': consultation_data.final_diagnosis or diagnosis_result['primary_diagnosis'],
            'notes': consultation_data.notes or ''
        },
        'diagnosis_result': diagnosis_result
    }

def consultation_controller(app):
    """Регистрация маршрутов для работы с консультациями"""

    @app.route('/consultation')
    @login_required
    def consultation():
        """Страница начала консультации"""
        patient_id = request.args.get('patient_id')
        db_session = None
        
        try:
            db_session = get_db_session()
            
            if not patient_id:
                # Показываем страницу выбора пациента
                from services.patient_service import PatientService
                patient_service = PatientService(db_session)
                patients = patient_service.get_all_patients()
                patients_data = [_prepare_patient_data(patient) for patient in patients]
                return render_template('consultation/consultation.html', patients=patients_data)
            
            # Начинаем консультацию с указанным пациентом
            from services.patient_service import PatientService
            consultation_service = ConsultationService(db_session)
            patient_service = PatientService(db_session)
            
            patient = patient_service.get_patient(int(patient_id))
            if not patient:
                return "Пациент не найден", 404
            
            doctor_id = session.get('doctor_id')
            consultation = consultation_service.start_consultation(int(patient_id), doctor_id)
            
            consultation_data = {
                'id': consultation.id,
                'sub_graph_find_diagnosis': consultation.sub_graph_find_diagnosis
            }
            
            return render_template('consultation/consultation.html', 
                                 patient=_prepare_patient_data(patient),
                                 consultation=consultation_data)
            
        except Exception as e:
            print(f"Ошибка при начале консультации: {str(e)}")
            import traceback
            traceback.print_exc()
            return render_template('consultation/consultation.html', patients=[])
        finally:
            if db_session:
                db_session.close()

    @app.route('/consultation/result')
    @login_required
    def consultation_result():
        """Страница результатов консультации"""
        consultation_id = request.args.get('consultation_id')
        
        if not consultation_id:
            return "Консультация не указана", 400
        
        db_session = None
        try:
            consultation_service, db_session = _get_consultation_service()
            
            result = consultation_service.get_consultation_result(int(consultation_id))
            if not result:
                return "Консультация не найдена", 404
            
            consultation_data = result['consultation']
            diagnosis_result = prepare_consultation_data(consultation_data)
            
            template_data = _prepare_consultation_result_data(consultation_data, diagnosis_result)
            
            return render_template('consultation/consultation-result.html',
                                consultation=consultation_data,
                                **template_data)
            
        except Exception as e:
            print(f"Ошибка при загрузке результатов консультации: {str(e)}")
            import traceback
            traceback.print_exc()
            return "Ошибка при загрузке страницы", 500
        finally:
            if db_session:
                db_session.close()

    @app.route('/api/consultation/save-answer', methods=['POST'])
    @login_required
    def api_save_answer():
        consultation_service, db_session = _get_consultation_service()
        try:
            data = request.get_json()
            print(f"Save answer request: {data}")
            
            if not data or 'consultation_id' not in data or 'answer' not in data:
                return _json_response(False, 'Отсутствуют обязательные данные', status_code=400)
            
            consultation = consultation_service.save_consultation_answer(
                data['consultation_id'],
                data['answer']
            )
            
            progress = consultation_service.get_consultation_progress(data['consultation_id'])
            next_question = consultation_service.get_current_question(data['consultation_id'])
            
            print(f"Next question after save: {next_question}")
            
            response_data = {
                'progress': progress,
                'next_question': next_question
            }
            
            if next_question and next_question.get('is_final'):
                diagnosis_data = consultation.sub_graph_find_diagnosis or {}
                response_data['diagnosis_candidate'] = diagnosis_data.get('final_diagnosis_candidate')
                print(f"Diagnosis candidate: {response_data['diagnosis_candidate']}")
            
            return _json_response(True, 'Ответ сохранен', response_data)
            
        except ValueError as e:
            print(f"ValueError: {str(e)}")
            return _json_response(False, str(e), status_code=400)
        except Exception as e:
            print(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return _json_response(False, f'Ошибка при сохранении ответа: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/consultation/complete', methods=['POST'])
    @login_required
    def api_complete_consultation():
        """Завершение консультации"""
        consultation_service, db_session = _get_consultation_service()
        try:
            data = request.get_json()
            
            if not data or 'consultation_id' not in data:
                return _json_response(False, 'ID консультации обязателен', status_code=400)
            
            consultation = consultation_service.complete_consultation(
                data['consultation_id'],
                data.get('final_diagnosis'),
                data.get('notes')
            )
            
            return _json_response(True, 'Консультация завершена', {
                'consultation': {
                    'id': consultation.id,
                    'final_diagnosis': consultation.final_diagnosis,
                    'status': consultation.status
                }
            })
            
        except ValueError as e:
            return _json_response(False, str(e), status_code=400)
        except Exception as e:
            return _json_response(False, f'Ошибка при завершении консультации: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/consultation/<int:consultation_id>')
    @login_required
    def api_get_consultation(consultation_id):
        """Получение данных консультации"""
        consultation_service, db_session = _get_consultation_service()
        try:
            consultation = consultation_service.consultation_repository.get_consultation_by_id(consultation_id)
            
            if not consultation:
                return _json_response(False, 'Консультация не найдена', status_code=404)
            
            progress = consultation_service.get_consultation_progress(consultation_id)
            current_question = consultation_service.get_current_question(consultation_id)
            
            return _json_response(True, 'Данные консультации получены', {
                'consultation': {
                    'id': consultation.id,
                    'patient_id': consultation.patient_id,
                    'doctor_id': consultation.doctor_id,
                    'status': consultation.status,
                    'final_diagnosis': consultation.final_diagnosis,
                    'sub_graph_find_diagnosis': consultation.sub_graph_find_diagnosis,
                    'consultation_date': consultation.consultation_date.isoformat() if consultation.consultation_date else None,
                    'patient': {
                        'last_name': consultation.patient.last_name,
                        'first_name': consultation.patient.first_name,
                        'middle_name': consultation.patient.middle_name
                    } if consultation.patient else None
                },
                'progress': progress,
                'current_question': current_question
            })
            
        except Exception as e:
            return _json_response(False, f'Ошибка при получении данных консультации: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/consultation/cancel', methods=['POST'])
    @login_required
    def api_cancel_consultation():
        """Отмена консультации"""
        consultation_service, db_session = _get_consultation_service()
        try:
            data = request.get_json()
            
            if not data or 'consultation_id' not in data:
                return _json_response(False, 'ID консультации обязателен', status_code=400)
            
            consultation = consultation_service.cancel_consultation(data['consultation_id'])
            
            return _json_response(True, 'Консультация отменена', {
                'consultation': {
                    'id': consultation.id,
                    'status': consultation.status
                }
            })
            
        except ValueError as e:
            return _json_response(False, str(e), status_code=400)
        except Exception as e:
            return _json_response(False, f'Ошибка при отмене консультации: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/consultation/save-draft', methods=['POST'])
    @login_required
    def api_save_draft():
        """Сохранение консультации как черновика"""
        consultation_service, db_session = _get_consultation_service()
        try:
            data = request.get_json()
            
            if not data or 'consultation_id' not in data:
                return _json_response(False, 'ID консультации обязателен', status_code=400)
            
            consultation = consultation_service.save_as_draft(data['consultation_id'])
            
            return _json_response(True, 'Консультация сохранена как черновик', {
                'consultation': {
                    'id': consultation.id,
                    'status': consultation.status
                }
            })
            
        except ValueError as e:
            return _json_response(False, str(e), status_code=400)
        except Exception as e:
            return _json_response(False, f'Ошибка при сохранении черновика: {str(e)}', status_code=500)
        finally:
            db_session.close()

    @app.route('/api/consultations/my')
    @login_required
    def api_get_my_consultations():
        """Получение консультаций текущего врача"""
        consultation_service, db_session = _get_consultation_service()
        try:
            doctor_id = session.get('doctor_id')
            
            consultations = db_session.query(Consultation)\
                .options(joinedload(Consultation.patient))\
                .filter(Consultation.doctor_id == doctor_id)\
                .order_by(Consultation.consultation_date.desc())\
                .all()
            
            consultations_data = []
            for consultation in consultations:
                consultations_data.append({
                    'id': consultation.id,
                    'patient_name': f"{consultation.patient.last_name} {consultation.patient.first_name} {consultation.patient.middle_name or ''}".strip() if consultation.patient else 'Неизвестный пациент',
                    'final_diagnosis': consultation.final_diagnosis,
                    'status': consultation.status,
                    'consultation_date': consultation.consultation_date.isoformat() if consultation.consultation_date else None,
                    'patient_id': consultation.patient_id
                })
            
            return _json_response(True, 'Консультации получены', {
                'consultations': consultations_data
            })
            
        except Exception as e:
            return _json_response(False, f'Ошибка при получении консультаций: {str(e)}', status_code=500)
        finally:
            db_session.close()