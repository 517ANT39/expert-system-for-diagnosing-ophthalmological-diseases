import os
import json
from datetime import datetime
from repositories.consultation_repository import ConsultationRepository
from services.diagnosis_service import DiagnosisService

# Создаем единственный экземпляр DiagnosisService
_diagnosis_service_instance = None

def get_diagnosis_service():
    """Получение единственного экземпляра DiagnosisService"""
    global _diagnosis_service_instance
    if _diagnosis_service_instance is None:
        _diagnosis_service_instance = DiagnosisService()
    return _diagnosis_service_instance

class ConsultationService:
    def __init__(self, db_session):
        self.consultation_repository = ConsultationRepository(db_session)
        self.diagnosis_service = get_diagnosis_service()

    def start_consultation(self, patient_id: int, doctor_id: int):
        """Начало новой консультации"""
        
        # Проверяем активную консультацию
        active_consultation = self.consultation_repository.get_active_consultation(patient_id, doctor_id)
        
        if active_consultation:
            return active_consultation
        
        # Получаем первый вопрос
        first_question = self.diagnosis_service.get_initial_question()
        
        if not first_question:
            raise ValueError("Не удалось загрузить базу знаний")
        
        # Создаем консультацию
        consultation_data = {
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'status': 'active',
            'sub_graph_find_diagnosis': {
                'current_path': [],
                'current_question': first_question['text'],
                'answers': {},
                'started_at': datetime.utcnow().isoformat()
            }
        }
        
        consultation = self.consultation_repository.create_consultation(consultation_data)
        return consultation

    def save_consultation_answer(self, consultation_id: int, answer: str):
        """Сохранение ответа на вопрос и переход к следующему"""
        
        # Получаем консультацию
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        
        # Получаем текущий вопрос для сохранения
        current_question = self.diagnosis_service.get_question_by_path(current_path)
        
        if not current_question:
            raise ValueError("Текущий вопрос не найден")
        
        # Сохраняем ответ в историю
        question_number = len(diagnosis_data.get('answers', {})) + 1
        question_key = f"q{question_number}"
        
        if 'answers' not in diagnosis_data:
            diagnosis_data['answers'] = {}
        
        diagnosis_data['answers'][question_key] = {
            'question': current_question['text'],
            'answer': answer,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        
        # Получаем следующий вопрос
        next_question = self.diagnosis_service.get_next_question(current_path, answer)
        
        if not next_question:
            raise ValueError("Не удалось получить следующий вопрос")
        
        # ВАЖНО: Создаем КОПИЮ diagnosis_data для обновления
        updated_diagnosis_data = diagnosis_data.copy()
        updated_diagnosis_data['current_path'] = next_question['path']
        updated_diagnosis_data['current_question'] = next_question['text']
        
        # Если достигли конечного диагноза
        if next_question['is_final']:
            diagnosis = self.diagnosis_service.get_diagnosis(next_question['path'])
            updated_diagnosis_data['final_diagnosis_candidate'] = diagnosis
            updated_diagnosis_data['completed_at'] = datetime.utcnow().isoformat()
        
        # Обновляем консультацию в БД
        consultation_data = {
            'sub_graph_find_diagnosis': updated_diagnosis_data
        }
        
        updated_consultation = self.consultation_repository.update_consultation(consultation_id, consultation_data)
        
        # ПРОВЕРКА: Получаем обновленную консультацию из БД
        verification_consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        
        return updated_consultation

    def get_current_question(self, consultation_id: int):
        """Получение текущего вопроса консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            return None
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        question = self.diagnosis_service.get_question_by_path(current_path)
        return question

    def get_consultation_progress(self, consultation_id: int):
        """Получение прогресса консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            return None
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        answers = diagnosis_data.get('answers', {})
        current_path = diagnosis_data.get('current_path', [])
        
        total_questions = len(answers)
        progress = min((total_questions / 24) * 100, 100)
        
        # Получаем актуальный текущий вопрос через diagnosis_service
        current_question_obj = self.diagnosis_service.get_question_by_path(current_path)
        current_question = current_question_obj['text'] if current_question_obj else diagnosis_data.get('current_question', '')
        
        is_completed = consultation.status == 'completed'
        
        result = {
            'current_question': current_question,
            'progress_percent': progress,
            'questions_answered': total_questions,
            'is_completed': is_completed
        }
        
        return result

    def complete_consultation(self, consultation_id: int, final_diagnosis: str = None, notes: str = None):
        """Завершение консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        
        if not final_diagnosis and 'final_diagnosis_candidate' in diagnosis_data:
            final_diagnosis = diagnosis_data['final_diagnosis_candidate']
        
        # ВАЖНО: Устанавливаем статус 'completed' при завершении
        consultation_data = {
            'status': 'completed',
            'final_diagnosis': final_diagnosis,
            'notes': notes  # Сохраняем рекомендации врача
        }
        
        if 'completed_at' not in diagnosis_data:
            diagnosis_data['completed_at'] = datetime.utcnow().isoformat()
        
        consultation_data['sub_graph_find_diagnosis'] = diagnosis_data
        
        return self.consultation_repository.update_consultation(consultation_id, consultation_data)

    def cancel_consultation(self, consultation_id: int):
        """Отмена консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        consultation_data = {
            'status': 'canceled'
        }
        
        return self.consultation_repository.update_consultation(consultation_id, consultation_data)

    def save_as_draft(self, consultation_id: int):
        """Сохранение консультации как черновика"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        # Если консультация активна, но не завершена - сохраняем как черновик
        if consultation.status == 'active':
            consultation_data = {
                'status': 'draft'
            }
            return self.consultation_repository.update_consultation(consultation_id, consultation_data)
        
        return consultation

    def get_consultation_result(self, consultation_id: int):
        """Получение результатов консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            return None
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        # Получаем диагноз из графа
        graph_diagnosis = self.diagnosis_service.get_diagnosis(current_path)
        final_diagnosis = consultation.final_diagnosis or graph_diagnosis
        
        # Формируем историю вопросов-ответов
        qa_history = []
        answers = diagnosis_data.get('answers', {})
        for key, qa in sorted(answers.items()):
            qa_history.append({
                'question': qa['question'],
                'answer': qa['answer'],
                'timestamp': qa.get('timestamp')
            })
        
        # Генерируем рекомендации на основе диагноза
        recommendations = self._generate_recommendations(final_diagnosis)
        
        # Формируем объяснение диагноза
        explanation = self._generate_explanation(qa_history, final_diagnosis)
        
        # Формируем список симптомов для отображения
        symptoms_evidence = []
        for qa in qa_history:
            symptoms_evidence.append({
                'name': qa['question'],
                'present': qa['answer'] == 'yes'
            })
        
        return {
            'consultation': consultation,
            'diagnosis_result': {
                'primary_diagnosis': final_diagnosis,
                'confidence': self._calculate_confidence(qa_history),
                'explanation': explanation,
                'qa_history': qa_history,
                'recommendations': recommendations,
                'symptoms_evidence': symptoms_evidence
            }
        }

    def _calculate_confidence(self, qa_history: list) -> int:
        """Расчет уверенности в диагнозе"""
        if not qa_history:
            return 0
        
        total_questions = len(qa_history)
        return min(80 + (total_questions * 2), 95)

    def _generate_explanation(self, qa_history: list, diagnosis: str) -> str:
        """Генерация объяснения диагноза"""
        if not qa_history:
            return "Диагноз основан на базовых симптомах."
        
        positive_answers = [qa for qa in qa_history if qa['answer'] == 'yes']
        
        if positive_answers:
            symptoms = [qa['question'] for qa in positive_answers[:3]]
            symptoms_text = ", ".join(symptoms)
            return f"Диагноз '{diagnosis}' основан на наличии следующих симптомов: {symptoms_text}."
        else:
            return f"Диагноз '{diagnosis}' основан на отсутствии характерных симптомов других заболеваний."

    def _generate_recommendations(self, diagnosis: str) -> dict:
        """Генерация рекомендаций по диагнозу"""
        recommendations_db = {
            "Ирит": {
                'medication': ["Атропин 1%", "Дексаметазон 0.1%"],
                'general': ["Постельный режим", "Защита от света"]
            },
            "Бактериальный конъюнктивит": {
                'medication': ["Ципрофлоксацин 0.3%", "Тетрациклин 1%"],
                'general': ["Гигиена рук", "Исключение линз"]
            },
            "Катаракта": {
                'medication': ["Тауфон 4%"],
                'general': ["Солнцезащитные очки", "Контроль заболеваний"]
            }
        }
        
        for key, value in recommendations_db.items():
            if key.lower() in diagnosis.lower():
                return value
        
        return {
            'medication': ["Симптоматическое лечение"],
            'general': ["Наблюдение у офтальмолога"]
        }