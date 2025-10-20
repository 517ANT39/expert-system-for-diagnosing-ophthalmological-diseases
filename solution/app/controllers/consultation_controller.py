from flask import request, jsonify, session, render_template
from ..services.consultation_service import ConsultationService, get_diagnosis_service
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Предварительная инициализация сервиса
_diagnosis_service = get_diagnosis_service()

def get_db_session():
    """Создание сессии БД"""
    database_url = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/ophthalmology_db")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def login_required(f):
    """Декоратор для проверки авторизации"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Требуется авторизация'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def consultation_controller(app):
    """Регистрация маршрутов для работы с консультациями"""
    
    # HTML маршрут для начала консультации
    @app.route('/consultation')
    @login_required
    def consultation():
        """Страница начала консультации"""
        patient_id = request.args.get('patient_id')
        
        if not patient_id:
            # Если пациент не указан, показываем страницу выбора пациента
            try:
                db_session = get_db_session()
                from ..services.patient_service import PatientService
                patient_service = PatientService(db_session)
                patients = patient_service.get_all_patients()
                db_session.close()
                
                return render_template('consultation/consultation.html', patients=patients)
            except Exception as e:
                print(f"Ошибка при загрузке пациентов: {str(e)}")
                return render_template('consultation/consultation.html', patients=[])
        
        try:
            db_session = get_db_session()
            from ..services.consultation_service import ConsultationService
            from ..services.patient_service import PatientService
            
            consultation_service = ConsultationService(db_session)
            patient_service = PatientService(db_session)
            
            # Получаем данные пациента
            patient = patient_service.get_patient(int(patient_id))
            if not patient:
                db_session.close()
                return "Пациент не найден", 404
            
            # Начинаем новую консультацию
            doctor_id = session.get('doctor_id')
            consultation = consultation_service.start_consultation(int(patient_id), doctor_id)
            
            # Получаем прогресс консультации
            progress = consultation_service.get_consultation_progress(consultation.id)
            
            db_session.close()
            
            return render_template('consultation/consultation.html', 
                                 patient=patient,
                                 consultation=consultation,
                                 progress=progress)
            
        except Exception as e:
            print(f"Ошибка при начале консультации: {str(e)}")
            import traceback
            traceback.print_exc()
            return render_template('consultation/consultation.html')

    # HTML маршрут для результатов консультации
    @app.route('/consultation/result')
    @login_required
    def consultation_result():
        """Страница результатов консультации"""
        consultation_id = request.args.get('consultation_id')
        
        if not consultation_id:
            return "Консультация не указана", 400
        
        try:
            db_session = get_db_session()
            from ..services.consultation_service import ConsultationService
            
            consultation_service = ConsultationService(db_session)
            
            # Получаем результаты консультации
            result = consultation_service.get_consultation_result(int(consultation_id))
            if not result:
                db_session.close()
                return "Консультация не найдена", 404
            
            db_session.close()
            
            return render_template('consultation/consultation-result.html',
                                 consultation=result['consultation'],
                                 diagnosis_result=result['diagnosis_result'])
            
        except Exception as e:
            print(f"Ошибка при загрузке результатов консультации: {str(e)}")
            import traceback
            traceback.print_exc()
            return "Ошибка при загрузке страницы", 500

    # API маршрут для сохранения ответа
    @app.route('/api/consultation/save-answer', methods=['POST'])
    @login_required
    def api_save_answer():
        db_session = None
        try:
            db_session = get_db_session()
            consultation_service = ConsultationService(db_session)  # Будет использовать единственный diagnosis_service
            
            data = request.get_json()
            print(f"📨 Save answer request: {data}")
            
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
            
            print(f"📊 Progress after save: {progress}")
            print(f"❓ Next question after save: {next_question}")
            
            response_data = {
                'success': True,
                'message': 'Ответ сохранен',
                'progress': progress,
                'next_question': next_question  # Используем next_question из сервиса
            }
            
            # Если достигли диагноза
            if next_question and next_question.get('is_final'):
                diagnosis_data = consultation.sub_graph_find_diagnosis or {}
                response_data['diagnosis_candidate'] = diagnosis_data.get('final_diagnosis_candidate')
                print(f"🎯 Diagnosis candidate: {response_data['diagnosis_candidate']}")
            
            return jsonify(response_data), 200
            
        except ValueError as e:
            print(f"❌ ValueError: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
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
            from ..services.consultation_service import ConsultationService
            
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
            from ..services.consultation_service import ConsultationService
            
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