import os
import json
from datetime import datetime
from ..repositories.consultation_repository import ConsultationRepository
from ..services.diagnosis_service import DiagnosisService

# Создаем единственный экземпляр DiagnosisService
_diagnosis_service_instance = None

def get_diagnosis_service():
    """Получение единственного экземпляра DiagnosisService"""
    global _diagnosis_service_instance
    if _diagnosis_service_instance is None:
        _diagnosis_service_instance = DiagnosisService()
        print("🎯 DIAGNOSIS SERVICE SINGLETON CREATED")
    return _diagnosis_service_instance

class ConsultationService:
    def __init__(self, db_session):
        self.consultation_repository = ConsultationRepository(db_session)
        self.diagnosis_service = get_diagnosis_service()
        print("🎯 CONSULTATION SERVICE INITIALIZED - READY FOR USE!")

    def start_consultation(self, patient_id: int, doctor_id: int):
        """Начало новой консультации"""
        print(f"🚀 START_CONSULTATION: patient={patient_id}, doctor={doctor_id}")
        
        # Проверяем активную консультацию
        active_consultation = self.consultation_repository.get_active_consultation(patient_id, doctor_id)
        
        if active_consultation:
            print(f"📋 Using existing consultation: {active_consultation.id}")
            return active_consultation
        
        # Получаем первый вопрос
        first_question = self.diagnosis_service.get_initial_question()
        print(f"❓ First question from diagnosis service: {first_question}")
        
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
        print(f"✅ CREATED consultation: {consultation.id}")
        return consultation

    def save_consultation_answer(self, consultation_id: int, answer: str):
        """Сохранение ответа на вопрос и переход к следующему"""
        print(f"\n" + "="*50)
        print(f"🎯 SAVE_ANSWER CALLED: consultation={consultation_id}, answer='{answer}'")
        print(f"="*50)
        
        # Получаем консультацию
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        print(f"📍 Current path from DB: {current_path}")
        print(f"📝 Current diagnosis_data: {diagnosis_data}")
        
        # Получаем текущий вопрос для сохранения
        current_question = self.diagnosis_service.get_question_by_path(current_path)
        print(f"💬 Current question: {current_question}")
        
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
        
        print(f"📝 Saved answer {question_number}: '{answer}' for question: '{current_question['text']}'")
        
        # Получаем следующий вопрос
        print(f"🔍 Getting next question for path {current_path} with answer '{answer}'")
        next_question = self.diagnosis_service.get_next_question(current_path, answer)
        print(f"🔍 Next question result: {next_question}")
        
        if not next_question:
            raise ValueError("Не удалось получить следующий вопрос")
        
        # ВАЖНО: Создаем КОПИЮ diagnosis_data для обновления
        updated_diagnosis_data = diagnosis_data.copy()
        updated_diagnosis_data['current_path'] = next_question['path']
        updated_diagnosis_data['current_question'] = next_question['text']
        
        print(f"🔄 Updated path: {updated_diagnosis_data['current_path']}")
        print(f"🔄 Updated question: {updated_diagnosis_data['current_question']}")
        print(f"🎯 Is final: {next_question['is_final']}")
        
        # Если достигли конечного диагноза
        if next_question['is_final']:
            diagnosis = self.diagnosis_service.get_diagnosis(next_question['path'])
            updated_diagnosis_data['final_diagnosis_candidate'] = diagnosis
            updated_diagnosis_data['completed_at'] = datetime.utcnow().isoformat()
            print(f"🎉 FINAL DIAGNOSIS REACHED: {diagnosis}")
        
        # Обновляем консультацию в БД
        consultation_data = {
            'sub_graph_find_diagnosis': updated_diagnosis_data
        }
        
        print(f"💾 Saving to DB: {consultation_data}")
        updated_consultation = self.consultation_repository.update_consultation(consultation_id, consultation_data)
        
        # ПРОВЕРКА: Получаем обновленную консультацию из БД
        verification_consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        print(f"✅ VERIFICATION - Path in DB: {verification_consultation.sub_graph_find_diagnosis.get('current_path', [])}")
        print(f"✅ VERIFICATION - Question in DB: {verification_consultation.sub_graph_find_diagnosis.get('current_question', '')}")
        
        print(f"✅ ANSWER SAVED SUCCESSFULLY")
        print(f"="*50)
        
        return updated_consultation

    def get_current_question(self, consultation_id: int):
        """Получение текущего вопроса консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            return None
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        current_path = diagnosis_data.get('current_path', [])
        
        print(f"🔍 get_current_question: consultation_id={consultation_id}, path_from_db={current_path}")
        question = self.diagnosis_service.get_question_by_path(current_path)
        print(f"🔍 get_current_question result: {question}")
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
        progress = min((total_questions / 15) * 100, 100)
        
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
        
        print(f"📊 get_consultation_progress: path={current_path}, result={result}")
        return result

    def complete_consultation(self, consultation_id: int, final_diagnosis: str = None, notes: str = None):
        """Завершение консультации"""
        consultation = self.consultation_repository.get_consultation_by_id(consultation_id)
        if not consultation:
            raise ValueError("Консультация не найдена")
        
        diagnosis_data = consultation.sub_graph_find_diagnosis or {}
        
        if not final_diagnosis and 'final_diagnosis_candidate' in diagnosis_data:
            final_diagnosis = diagnosis_data['final_diagnosis_candidate']
        
        consultation_data = {
            'status': 'completed',
            'final_diagnosis': final_diagnosis,
            'notes': notes
        }
        
        if 'completed_at' not in diagnosis_data:
            diagnosis_data['completed_at'] = datetime.utcnow().isoformat()
        
        consultation_data['sub_graph_find_diagnosis'] = diagnosis_data
        
        return self.consultation_repository.update_consultation(consultation_id, consultation_data)

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