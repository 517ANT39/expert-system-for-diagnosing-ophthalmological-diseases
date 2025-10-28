from flask import request, session, render_template
from services.consultation_service import ConsultationService
from utils.database import get_db_session, login_required
from utils.consultation_helpers import prepare_consultation_data
from solution.app.utils.controller_helpers import json_response, prepare_consultation_patient_data, prepare_consultation_result_data
from models.database_models import Consultation
from sqlalchemy.orm import joinedload

def _get_consultation_service():
    """Вспомогательная функция для получения сервиса консультаций"""
    db_session = get_db_session()
    return ConsultationService(db_session), db_session

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
                patients_data = [prepare_consultation_patient_data(patient) for patient in patients]
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
                                 patient=prepare_consultation_patient_data(patient),
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
            
            template_data = prepare_consultation_result_data(consultation_data, diagnosis_result)
            
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
                return json_response(False, 'Отсутствуют обязательные данные', status_code=400)
            
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
            
            return json_response(True, 'Ответ сохранен', response_data)
            
        except ValueError as e:
            print(f"ValueError: {str(e)}")
            return json_response(False, str(e), status_code=400)
        except Exception as e:
            print(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return json_response(False, f'Ошибка при сохранении ответа: {str(e)}', status_code=500)
        finally:
            db_session.close()

    # Остальные методы остаются аналогичными с заменой _json_response на json_response
    @app.route('/api/consultation/complete', methods=['POST'])
    @login_required
    def api_complete_consultation():
        """Завершение консультации"""
        consultation_service, db_session = _get_consultation_service()
        try:
            data = request.get_json()
            
            if not data or 'consultation_id' not in data:
                return json_response(False, 'ID консультации обязателен', status_code=400)
            
            consultation = consultation_service.complete_consultation(
                data['consultation_id'],
                data.get('final_diagnosis'),
                data.get('notes')
            )
            
            return json_response(True, 'Консультация завершена', {
                'consultation': {
                    'id': consultation.id,
                    'final_diagnosis': consultation.final_diagnosis,
                    'status': consultation.status
                }
            })
            
        except ValueError as e:
            return json_response(False, str(e), status_code=400)
        except Exception as e:
            return json_response(False, f'Ошибка при завершении консультации: {str(e)}', status_code=500)
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
                return json_response(False, 'Консультация не найдена', status_code=404)
            
            progress = consultation_service.get_consultation_progress(consultation_id)
            current_question = consultation_service.get_current_question(consultation_id)
            
            return json_response(True, 'Данные консультации получены', {
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
            return json_response(False, f'Ошибка при получении данных консультации: {str(e)}', status_code=500)
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
                return json_response(False, 'ID консультации обязателен', status_code=400)
            
            consultation = consultation_service.cancel_consultation(data['consultation_id'])
            
            return json_response(True, 'Консультация отменена', {
                'consultation': {
                    'id': consultation.id,
                    'status': consultation.status
                }
            })
            
        except ValueError as e:
            return json_response(False, str(e), status_code=400)
        except Exception as e:
            return json_response(False, f'Ошибка при отмене консультации: {str(e)}', status_code=500)
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
                return json_response(False, 'ID консультации обязателен', status_code=400)
            
            consultation = consultation_service.save_as_draft(data['consultation_id'])
            
            return json_response(True, 'Консультация сохранена как черновик', {
                'consultation': {
                    'id': consultation.id,
                    'status': consultation.status
                }
            })
            
        except ValueError as e:
            return json_response(False, str(e), status_code=400)
        except Exception as e:
            return json_response(False, f'Ошибка при сохранении черновика: {str(e)}', status_code=500)
        finally:
            db_session.close()