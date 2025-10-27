from flask import request, jsonify, session, render_template
from services.consultation_service import ConsultationService, get_diagnosis_service
from utils.database import get_db_session, login_required, _calculate_age
from utils.consultation_helpers import prepare_consultation_data
import os

# Предварительная инициализация сервиса
_diagnosis_service = get_diagnosis_service()

def consultation_controller(app):
    """Регистрация маршрутов для работы с консультациями"""
    
    # HTML маршрут для начала консультации
    @app.route('/consultation')
    @login_required
    def consultation():
        """Страница начала консультации"""
        patient_id = request.args.get('patient_id')
        db_session = None
        
        try:
            db_session = get_db_session()
            
            if not patient_id:
                # Если пациент не указан, показываем страницу выбора пациента
                from services.patient_service import PatientService
                patient_service = PatientService(db_session)
                patients = patient_service.get_all_patients()
                
                # Подготавливаем данные пациентов для шаблона
                patients_data = []
                for patient in patients:
                    patient_data = {
                        'id': patient.id,
                        'last_name': patient.last_name,
                        'first_name': patient.first_name,
                        'middle_name': patient.middle_name,
                        'birthday': patient.birthday,
                        'age': _calculate_age(patient.birthday) if patient.birthday else None
                    }
                    patients_data.append(patient_data)
                
                return render_template('consultation/consultation.html', patients=patients_data)
            
            # Если пациент указан
            from services.consultation_service import ConsultationService
            from services.patient_service import PatientService
            
            consultation_service = ConsultationService(db_session)
            patient_service = PatientService(db_session)
            
            # Получаем данные пациента
            patient = patient_service.get_patient(int(patient_id))
            if not patient:
                return "Пациент не найден", 404
            
            # Подготавливаем данные пациента для шаблона
            patient_data = {
                'id': patient.id,
                'last_name': patient.last_name,
                'first_name': patient.first_name,
                'middle_name': patient.middle_name,
                'birthday': patient.birthday,
                'age': _calculate_age(patient.birthday) if patient.birthday else None
            }
            
            # Начинаем новую консультацию
            doctor_id = session.get('doctor_id')
            consultation = consultation_service.start_consultation(int(patient_id), doctor_id)
            
            # Подготавливаем данные консультации для шаблона
            consultation_data = {
                'id': consultation.id,
                'sub_graph_find_diagnosis': consultation.sub_graph_find_diagnosis
            }
            
            return render_template('consultation/consultation.html', 
                                 patient=patient_data,
                                 consultation=consultation_data)
            
        except Exception as e:
            print(f"Ошибка при начале консультации: {str(e)}")
            import traceback
            traceback.print_exc()
            return render_template('consultation/consultation.html', patients=[])
        finally:
            if db_session:
                db_session.close()

    # HTML маршрут для результатов консультации
    @app.route('/consultation/result')
    @login_required
    def consultation_result():
        """Страница результатов консультации"""
        consultation_id = request.args.get('consultation_id')
        
        if not consultation_id:
            return "Консультация не указана", 400
        
        db_session = None
        try:
            db_session = get_db_session()
            from services.consultation_service import ConsultationService
            
            consultation_service = ConsultationService(db_session)
            
            # Получаем результаты консультации
            result = consultation_service.get_consultation_result(int(consultation_id))
            if not result:
                return "Консультация не найдена", 404
            
            # Форматируем данные для шаблона
            consultation_data = result['consultation']
            
            # Используем единую функцию для подготовки данных
            diagnosis_result = prepare_consultation_data(consultation_data)
            
            print("=== HTML DIAGNOSIS RESULT ===")
            print(f"diagnosis_result: {diagnosis_result}")
            print(f"symptoms_evidence count: {len(diagnosis_result['symptoms_evidence'])}")
            
            # Подготавливаем данные пациента
            patient = consultation_data.patient
            patient_data = {
                'name': f"{patient.last_name} {patient.first_name} {patient.middle_name or ''}".strip(),
                'birth_date': patient.birthday.strftime('%d.%m.%Y') if patient.birthday else 'Не указана',
                'sex': patient.sex,
                'age': _calculate_age(patient.birthday) if patient.birthday else None
            }
            
            # Подготавливаем данные врача
            doctor = consultation_data.doctor
            doctor_data = {
                'name': f"{doctor.last_name} {doctor.first_name} {doctor.middle_name or ''}".strip(),
                'qualification': "Врач-офтальмолог"
            }
            
            # Подготавливаем данные консультации
            from datetime import datetime
            consultation_info = {
                'date': consultation_data.consultation_date.strftime('%d.%m.%Y %H:%M') if consultation_data.consultation_date else datetime.now().strftime('%d.%m.%Y %H:%M'),
                'final_diagnosis': consultation_data.final_diagnosis or diagnosis_result['primary_diagnosis'],
                'notes': consultation_data.notes or ''
            }
            
            return render_template('consultation/consultation-result.html',
                                consultation=consultation_data,
                                patient=patient_data,
                                doctor=doctor_data,
                                consultation_info=consultation_info,
                                diagnosis_result=diagnosis_result)
            
        except Exception as e:
            print(f"Ошибка при загрузке результатов консультации: {str(e)}")
            import traceback
            traceback.print_exc()
            return "Ошибка при загрузке страницы", 500
        finally:
            if db_session:
                db_session.close()

    # Остальные API маршруты остаются без изменений...
    @app.route('/api/consultation/save-answer', methods=['POST'])
    @login_required
    def api_save_answer():
        db_session = None
        try:
            db_session = get_db_session()
            consultation_service = ConsultationService(db_session)
            
            data = request.get_json()
            print(f"Save answer request: {data}")
            
            if not data or 'consultation_id' not in data or 'answer' not in data:
                return jsonify({
                    'success': False,
                    'message': 'Отсутствуют обязательные данные'
                }), 400
            
            # Сохраняем ответ
            consultation = consultation_service.save_consultation_answer(
                data['consultation_id'],
                data['answer']
            )
            
            # Получаем обновленные данные
            progress = consultation_service.get_consultation_progress(data['consultation_id'])
            next_question = consultation_service.get_current_question(data['consultation_id'])
            
            print(f"Next question after save: {next_question}")
            
            response_data = {
                'success': True,
                'message': 'Ответ сохранен',
                'progress': progress,
                'next_question': next_question
            }
            
            # Если достигли диагноза
            if next_question and next_question.get('is_final'):
                diagnosis_data = consultation.sub_graph_find_diagnosis or {}
                response_data['diagnosis_candidate'] = diagnosis_data.get('final_diagnosis_candidate')
                print(f"Diagnosis candidate: {response_data['diagnosis_candidate']}")
            
            return jsonify(response_data), 200
            
        except ValueError as e:
            print(f"ValueError: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            print(f"Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'Ошибка при сохранении ответа: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    # API маршрут для завершения консультации
    @app.route('/api/consultation/complete', methods=['POST'])
    @login_required
    def api_complete_consultation():
        """Завершение консультации"""
        db_session = None
        try:
            db_session = get_db_session()
            from services.consultation_service import ConsultationService
            
            consultation_service = ConsultationService(db_session)
            
            data = request.get_json()
            
            if not data or 'consultation_id' not in data:
                return jsonify({
                    'success': False,
                    'message': 'ID консультации обязателен'
                }), 400
            
            consultation = consultation_service.complete_consultation(
                data['consultation_id'],
                data.get('final_diagnosis'),
                data.get('notes')
            )
            
            return jsonify({
                'success': True,
                'message': 'Консультация завершена',
                'consultation': {
                    'id': consultation.id,
                    'final_diagnosis': consultation.final_diagnosis,
                    'status': consultation.status
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
                'message': f'Ошибка при завершении консультации: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    # API маршрут для получения данных консультации
    @app.route('/api/consultation/<int:consultation_id>')
    @login_required
    def api_get_consultation(consultation_id):
        """Получение данных консультации"""
        db_session = None
        try:
            db_session = get_db_session()
            from services.consultation_service import ConsultationService
            
            consultation_service = ConsultationService(db_session)
            
            consultation = consultation_service.consultation_repository.get_consultation_by_id(consultation_id)
            
            if not consultation:
                return jsonify({
                    'success': False,
                    'message': 'Консультация не найдена'
                }), 404
            
            progress = consultation_service.get_consultation_progress(consultation_id)
            current_question = consultation_service.get_current_question(consultation_id)
            
            return jsonify({
                'success': True,
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
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Ошибка при получении данных консультации: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    # API маршрут для отмены консультации
    @app.route('/api/consultation/cancel', methods=['POST'])
    @login_required
    def api_cancel_consultation():
        """Отмена консультации"""
        db_session = None
        try:
            db_session = get_db_session()
            from services.consultation_service import ConsultationService
            
            consultation_service = ConsultationService(db_session)
            
            data = request.get_json()
            
            if not data or 'consultation_id' not in data:
                return jsonify({
                    'success': False,
                    'message': 'ID консультации обязателен'
                }), 400
            
            consultation = consultation_service.cancel_consultation(data['consultation_id'])
            
            return jsonify({
                'success': True,
                'message': 'Консультация отменена',
                'consultation': {
                    'id': consultation.id,
                    'status': consultation.status
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
                'message': f'Ошибка при отмене консультации: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()

    # API маршрут для сохранения как черновика
    @app.route('/api/consultation/save-draft', methods=['POST'])
    @login_required
    def api_save_draft():
        """Сохранение консультации как черновика"""
        db_session = None
        try:
            db_session = get_db_session()
            from services.consultation_service import ConsultationService
            
            consultation_service = ConsultationService(db_session)
            
            data = request.get_json()
            
            if not data or 'consultation_id' not in data:
                return jsonify({
                    'success': False,
                    'message': 'ID консультации обязателен'
                }), 400
            
            consultation = consultation_service.save_as_draft(data['consultation_id'])
            
            return jsonify({
                'success': True,
                'message': 'Консультация сохранена как черновик',
                'consultation': {
                    'id': consultation.id,
                    'status': consultation.status
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
                'message': f'Ошибка при сохранении черновика: {str(e)}'
            }), 500
        finally:
            if db_session:
                db_session.close()